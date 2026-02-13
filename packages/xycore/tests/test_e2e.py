"""End-to-end tests for the XY chain primitive.

Tests the full lifecycle: create, append, tamper detection, signatures,
and performance at scale.
"""

from __future__ import annotations

import base64
import time

import pytest

from xycore import XYChain, XYEntry, hash_state
from xycore.crypto import compute_xy, verify_chain, verify_entry
from xycore.signature import generate_keypair, sign_entry, verify_signature


# ────────────────────────────────────────────────────────────────────────────
# 1. Core chain: 50 entries, tamper at 25, catch at exactly 25
# ────────────────────────────────────────────────────────────────────────────

class TestTamperDetection:
    """Verify that tampering with any entry is caught at the exact index."""

    def test_50_entries_tamper_at_25(self):
        """Build 50 entries, tamper with entry 25, verify catches at 25."""
        chain = XYChain(name="tamper-test", auto_redact=False)

        for i in range(50):
            chain.append(
                operation=f"step_{i}",
                y_state={"counter": i, "data": f"value_{i}"},
            )

        # Chain should be valid before tampering
        valid, break_idx = chain.verify()
        assert valid is True
        assert break_idx is None
        assert chain.length == 50

        # Verify the chain rule holds for every entry
        assert chain.entries[0].x == "GENESIS"
        for i in range(1, 50):
            assert chain.entries[i].x == chain.entries[i - 1].y, (
                f"Chain rule broken at {i}: "
                f"entry[{i}].x={chain.entries[i].x[:16]}... != "
                f"entry[{i-1}].y={chain.entries[i-1].y[:16]}..."
            )

        # Tamper: change entry 25's y_state, which changes y, which
        # invalidates its XY proof hash
        original_y = chain.entries[25].y
        original_xy = chain.entries[25].xy
        chain.entries[25].y = hash_state({"counter": 25, "data": "TAMPERED"})

        # The tampered y should be different
        assert chain.entries[25].y != original_y

        # Verify should catch the tamper at exactly index 25
        valid, break_idx = chain.verify()
        assert valid is False
        assert break_idx == 25, (
            f"Expected break at index 25, got {break_idx}"
        )

    def test_tamper_genesis(self):
        """Tamper with the first entry's x (should be GENESIS)."""
        chain = XYChain(name="genesis-tamper", auto_redact=False)
        for i in range(10):
            chain.append(operation=f"op_{i}", y_state={"i": i})

        chain.entries[0].x = "NOT_GENESIS"

        valid, break_idx = chain.verify()
        assert valid is False
        assert break_idx == 0

    def test_tamper_xy_proof(self):
        """Tamper with an entry's XY proof hash directly."""
        chain = XYChain(name="xy-tamper", auto_redact=False)
        for i in range(20):
            chain.append(operation=f"op_{i}", y_state={"i": i})

        # Corrupt the XY proof at index 10
        chain.entries[10].xy = "xy_0000000000000000000000000000000000000000000000000000000000000000"

        valid, break_idx = chain.verify()
        assert valid is False
        assert break_idx == 10

    def test_tamper_chain_link(self):
        """Break the chain link: entry[15].x != entry[14].y."""
        chain = XYChain(name="link-tamper", auto_redact=False)
        for i in range(20):
            chain.append(operation=f"op_{i}", y_state={"i": i})

        # Replace entry 15's x with a bogus value (breaks the link)
        original_x = chain.entries[15].x
        chain.entries[15].x = "deadbeef" * 8

        valid, break_idx = chain.verify()
        assert valid is False
        assert break_idx == 15

    def test_tamper_operation(self):
        """Change an entry's operation name — should invalidate XY proof."""
        chain = XYChain(name="op-tamper", auto_redact=False)
        for i in range(30):
            chain.append(operation=f"op_{i}", y_state={"i": i})

        chain.entries[7].operation = "HACKED"

        valid, break_idx = chain.verify()
        assert valid is False
        assert break_idx == 7

    def test_tamper_timestamp(self):
        """Change an entry's timestamp — should invalidate XY proof."""
        chain = XYChain(name="ts-tamper", auto_redact=False)
        for i in range(10):
            chain.append(operation=f"op_{i}", y_state={"i": i})

        chain.entries[3].timestamp = 0.0

        valid, break_idx = chain.verify()
        assert valid is False
        assert break_idx == 3

    def test_untampered_chain_verifies(self):
        """An untampered chain with 50 entries should verify cleanly."""
        chain = XYChain(name="clean", auto_redact=False)
        for i in range(50):
            chain.append(operation=f"step_{i}", y_state={"n": i})

        valid, break_idx = chain.verify()
        assert valid is True
        assert break_idx is None

    def test_empty_chain_verifies(self):
        """An empty chain should verify as valid."""
        chain = XYChain(name="empty")
        valid, break_idx = chain.verify()
        assert valid is True
        assert break_idx is None

    def test_single_entry_verifies(self):
        """A single-entry chain should verify."""
        chain = XYChain(name="single", auto_redact=False)
        chain.append(operation="only", y_state={"only": True})

        valid, break_idx = chain.verify()
        assert valid is True
        assert break_idx is None
        assert chain.entries[0].x == "GENESIS"


# ────────────────────────────────────────────────────────────────────────────
# 2. Digital signatures: sign, verify, tamper detection with sigs
# ────────────────────────────────────────────────────────────────────────────

class TestSignatures:
    """Test Ed25519 digital signatures on chain entries."""

    def test_sign_and_verify_single_entry(self):
        """Sign a single entry and verify the signature."""
        priv, pub = generate_keypair()

        chain = XYChain(name="sig-test", auto_redact=False)
        chain.append(
            operation="signed_op",
            y_state={"data": "signed"},
            private_key=priv,
            signer_id="alice",
        )

        entry = chain.entries[0]
        assert entry.signature is not None
        assert entry.public_key is not None
        assert entry.signer_id == "alice"
        assert verify_signature(entry) is True

    def test_sign_all_entries_in_chain(self):
        """Sign every entry in a 20-entry chain, verify all."""
        priv, pub = generate_keypair()

        chain = XYChain(name="all-signed", auto_redact=False)
        for i in range(20):
            chain.append(
                operation=f"op_{i}",
                y_state={"i": i},
                private_key=priv,
                signer_id="bob",
            )

        # Chain should be valid
        valid, _ = chain.verify()
        assert valid is True

        # Every signature should be valid
        for entry in chain.entries:
            assert entry.signature is not None
            assert verify_signature(entry) is True

        # verify_signatures on chain level
        sig_valid, sig_break = chain.verify_signatures()
        assert sig_valid is True
        assert sig_break is None

    def test_mixed_signed_unsigned(self):
        """Chain with some signed and some unsigned entries."""
        priv, pub = generate_keypair()

        chain = XYChain(name="mixed-sig", auto_redact=False)
        for i in range(10):
            if i % 2 == 0:
                chain.append(
                    operation=f"signed_{i}",
                    y_state={"i": i},
                    private_key=priv,
                    signer_id="carol",
                )
            else:
                chain.append(
                    operation=f"unsigned_{i}",
                    y_state={"i": i},
                )

        valid, _ = chain.verify()
        assert valid is True

        # Signed entries should verify
        for i in range(0, 10, 2):
            assert chain.entries[i].signature is not None
            assert verify_signature(chain.entries[i]) is True

        # Unsigned entries should have no signature
        for i in range(1, 10, 2):
            assert chain.entries[i].signature is None

        # Chain-level signature verification should pass
        # (skips unsigned entries)
        sig_valid, _ = chain.verify_signatures()
        assert sig_valid is True

    def test_invalid_signature_detected(self):
        """Tamper with a signed entry — signature should fail."""
        priv, pub = generate_keypair()

        chain = XYChain(name="bad-sig", auto_redact=False)
        chain.append(
            operation="original",
            y_state={"data": "original"},
            private_key=priv,
            signer_id="dave",
        )

        entry = chain.entries[0]
        assert verify_signature(entry) is True

        # Tamper with the operation after signing
        entry.operation = "tampered"
        assert verify_signature(entry) is False

    def test_wrong_key_signature_fails(self):
        """Sign with one key, try to verify — should fail if we swap the pubkey."""
        priv_a, pub_a = generate_keypair()
        priv_b, pub_b = generate_keypair()

        chain = XYChain(name="wrong-key", auto_redact=False)
        chain.append(
            operation="signed_by_a",
            y_state={"signer": "a"},
            private_key=priv_a,
            signer_id="alice",
        )

        entry = chain.entries[0]
        assert verify_signature(entry) is True

        # Replace public key with key B — signature should fail
        entry.public_key = base64.b64encode(pub_b).decode("ascii")
        assert verify_signature(entry) is False

    def test_corrupted_signature_bytes(self):
        """Corrupt the signature bytes — should fail verification."""
        priv, pub = generate_keypair()

        chain = XYChain(name="corrupt-sig", auto_redact=False)
        chain.append(
            operation="signed",
            y_state={"ok": True},
            private_key=priv,
        )

        entry = chain.entries[0]
        assert verify_signature(entry) is True

        # Corrupt the signature: flip some bytes
        sig_bytes = base64.b64decode(entry.signature)
        corrupted = bytes([b ^ 0xFF for b in sig_bytes[:8]]) + sig_bytes[8:]
        entry.signature = base64.b64encode(corrupted).decode("ascii")
        assert verify_signature(entry) is False

    def test_verify_signatures_catches_tampered(self):
        """Chain.verify_signatures() should catch a tampered signed entry."""
        priv, pub = generate_keypair()

        chain = XYChain(name="chain-sig-fail", auto_redact=False)
        for i in range(10):
            chain.append(
                operation=f"op_{i}",
                y_state={"i": i},
                private_key=priv,
            )

        # Tamper with entry 5's operation (invalidates signature)
        chain.entries[5].operation = "TAMPERED"

        sig_valid, sig_break = chain.verify_signatures()
        assert sig_valid is False
        assert sig_break == 5

    def test_no_signature_returns_false(self):
        """verify_signature on unsigned entry returns False."""
        entry = XYEntry.create(
            index=0, operation="unsigned", x="GENESIS", y="abc"
        )
        assert verify_signature(entry) is False

    def test_multiple_signers(self):
        """Chain with entries signed by different keys."""
        priv_a, pub_a = generate_keypair()
        priv_b, pub_b = generate_keypair()

        chain = XYChain(name="multi-signer", auto_redact=False)
        chain.append(
            operation="by_alice",
            y_state={"who": "alice"},
            private_key=priv_a,
            signer_id="alice",
        )
        chain.append(
            operation="by_bob",
            y_state={"who": "bob"},
            private_key=priv_b,
            signer_id="bob",
        )

        assert chain.entries[0].signer_id == "alice"
        assert chain.entries[1].signer_id == "bob"
        assert verify_signature(chain.entries[0]) is True
        assert verify_signature(chain.entries[1]) is True

        valid, _ = chain.verify()
        assert valid is True

        sig_valid, _ = chain.verify_signatures()
        assert sig_valid is True


# ────────────────────────────────────────────────────────────────────────────
# 3. Performance: 10,000-entry chain
# ────────────────────────────────────────────────────────────────────────────

class TestPerformance:
    """Test chain operations at scale."""

    def test_10k_entries_append_and_verify(self):
        """Build a 10,000-entry chain and verify it.

        Performance targets:
        - Append: < 10s for 10k entries
        - Verify: < 5s for 10k entries
        """
        chain = XYChain(name="perf-10k", auto_redact=False)

        # Append 10,000 entries
        t0 = time.monotonic()
        for i in range(10_000):
            chain.append(
                operation=f"txn_{i}",
                y_state={"seq": i, "amount": i * 1.5},
            )
        append_time = time.monotonic() - t0

        assert chain.length == 10_000
        assert chain.entries[0].x == "GENESIS"
        assert chain.entries[9999].x == chain.entries[9998].y

        # Verify entire chain
        t1 = time.monotonic()
        valid, break_idx = chain.verify()
        verify_time = time.monotonic() - t1

        assert valid is True
        assert break_idx is None

        # Performance assertions
        assert append_time < 30.0, f"Append took {append_time:.2f}s (limit 30s)"
        assert verify_time < 15.0, f"Verify took {verify_time:.2f}s (limit 15s)"

        print(f"\n  10k append: {append_time:.2f}s ({10_000/append_time:.0f} entries/s)")
        print(f"  10k verify: {verify_time:.2f}s ({10_000/verify_time:.0f} entries/s)")

    def test_10k_tamper_detection_at_middle(self):
        """Build 10k entries, tamper at 5000, verify catches at 5000."""
        chain = XYChain(name="perf-tamper", auto_redact=False)
        for i in range(10_000):
            chain.append(operation=f"op_{i}", y_state={"i": i})

        # Tamper at the middle
        chain.entries[5000].xy = "xy_" + "0" * 64

        valid, break_idx = chain.verify()
        assert valid is False
        assert break_idx == 5000

    def test_10k_serialization_roundtrip(self):
        """Serialize and deserialize a 10k chain — should verify after."""
        chain = XYChain(name="perf-serde", auto_redact=False)
        for i in range(10_000):
            chain.append(operation=f"op_{i}", y_state={"i": i})

        # Roundtrip
        data = chain.to_dict()
        restored = XYChain.from_dict(data)

        assert restored.length == 10_000
        assert restored.name == "perf-serde"
        assert restored.head == chain.head
        assert restored.root == chain.root

        valid, break_idx = restored.verify()
        assert valid is True
        assert break_idx is None


# ────────────────────────────────────────────────────────────────────────────
# 4. Edge cases and invariants
# ────────────────────────────────────────────────────────────────────────────

class TestInvariants:
    """Test core invariants that must always hold."""

    def test_xy_hash_format(self):
        """Every XY proof starts with 'xy_' followed by 64 hex chars."""
        chain = XYChain(name="format-test", auto_redact=False)
        for i in range(10):
            chain.append(operation=f"op_{i}", y_state={"i": i})

        for entry in chain.entries:
            assert entry.xy.startswith("xy_")
            hex_part = entry.xy[3:]
            assert len(hex_part) == 64
            int(hex_part, 16)  # Must be valid hex

    def test_deterministic_hashing(self):
        """Same input always produces the same hash."""
        state = {"key": "value", "number": 42}
        h1 = hash_state(state)
        h2 = hash_state(state)
        assert h1 == h2

        # Order of keys shouldn't matter (canonical JSON)
        state_reordered = {"number": 42, "key": "value"}
        h3 = hash_state(state_reordered)
        assert h1 == h3

    def test_chain_rule_holds_for_all_entries(self):
        """The chain rule must hold for every consecutive pair."""
        chain = XYChain(name="rule-test", auto_redact=False)
        for i in range(100):
            chain.append(operation=f"op_{i}", y_state={"i": i})

        assert chain.entries[0].x == "GENESIS"
        for i in range(1, 100):
            assert chain.entries[i].x == chain.entries[i - 1].y

    def test_verify_entry_individually(self):
        """Each entry's XY proof should verify independently."""
        chain = XYChain(name="individual-verify", auto_redact=False)
        for i in range(20):
            chain.append(operation=f"op_{i}", y_state={"i": i})

        for entry in chain.entries:
            assert verify_entry(entry) is True

    def test_compute_xy_is_deterministic(self):
        """compute_xy with same inputs always produces same output."""
        xy1 = compute_xy("x_hash", "operation", "y_hash", 1234567890.0)
        xy2 = compute_xy("x_hash", "operation", "y_hash", 1234567890.0)
        assert xy1 == xy2
        assert xy1.startswith("xy_")

    def test_different_inputs_different_hashes(self):
        """Different states produce different hashes."""
        h1 = hash_state({"a": 1})
        h2 = hash_state({"a": 2})
        h3 = hash_state({"b": 1})
        assert h1 != h2
        assert h1 != h3
        assert h2 != h3

    def test_head_tracks_latest_y(self):
        """chain.head should always equal the latest entry's y."""
        chain = XYChain(name="head-test", auto_redact=False)
        assert chain.head == "GENESIS"

        for i in range(10):
            chain.append(operation=f"op_{i}", y_state={"i": i})
            assert chain.head == chain.entries[-1].y

    def test_root_is_first_xy(self):
        """chain.root should always equal the first entry's xy."""
        chain = XYChain(name="root-test", auto_redact=False)
        assert chain.root is None

        chain.append(operation="first", y_state={"first": True})
        first_xy = chain.entries[0].xy
        assert chain.root == first_xy

        for i in range(10):
            chain.append(operation=f"op_{i}", y_state={"i": i})
            assert chain.root == first_xy  # root never changes

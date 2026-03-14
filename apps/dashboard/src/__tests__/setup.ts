import "@testing-library/jest-dom/vitest";
import React from "react";

// Mock next/navigation
vi.mock("next/navigation", () => ({
  useParams: vi.fn(() => ({})),
  useRouter: vi.fn(() => ({
    push: vi.fn(),
    replace: vi.fn(),
    back: vi.fn(),
  })),
  useSearchParams: vi.fn(() => new URLSearchParams()),
  usePathname: vi.fn(() => "/"),
}));

// Mock framer-motion to avoid animation issues in tests
vi.mock("framer-motion", () => ({
  motion: {
    div: React.forwardRef(function MotionDiv(
      props: Record<string, unknown> & { children?: React.ReactNode },
      ref: React.Ref<HTMLDivElement>
    ) {
      const {
        initial,
        animate,
        exit,
        transition,
        whileHover,
        whileTap,
        children,
        ...rest
      } = props;
      return React.createElement("div", { ...rest, ref }, children);
    }),
  },
  AnimatePresence: ({ children }: { children?: React.ReactNode }) => children,
}));

// Mock clipboard API
Object.defineProperty(navigator, "clipboard", {
  value: { writeText: vi.fn().mockResolvedValue(undefined) },
  writable: true,
  configurable: true,
});

// Web Crypto API — ensure it's available in jsdom
if (!globalThis.crypto?.subtle) {
  // eslint-disable-next-line @typescript-eslint/no-require-imports
  const { webcrypto } = require("node:crypto");
  Object.defineProperty(globalThis, "crypto", {
    value: webcrypto,
  });
}

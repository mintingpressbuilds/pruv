import Link from "next/link";

export function Footer() {
  return (
    <footer className="footer">
      <div className="container">
        <div className="footer-primitive">X &rarr; Y &rarr; Proof.</div>
        <div className="footer-links">
          <a href="https://docs.pruv.dev">docs</a>
          <a href="https://app.pruv.dev">dashboard</a>
          <a href="https://github.com/mintingpressbuilds/pruv">github</a>
          <a href="https://api.pruv.dev/docs">api</a>
          <Link href="/privacy">privacy</Link>
          <Link href="/terms">terms</Link>
        </div>
      </div>
    </footer>
  );
}

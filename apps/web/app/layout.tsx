import "./globals.css";
import Link from "next/link";

export const metadata = {
  title: "ClaimVault",
  description: "Parad0x Labs custody and compliance claim center",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <div className="bg-slate-50 text-slate-900 min-h-screen flex flex-col">
          <header className="border-b border-slate-200 bg-white">
            <div className="mx-auto flex max-w-5xl items-center justify-between px-4 py-3">
              <div className="text-lg font-semibold text-slate-800">ClaimVault</div>
              <nav className="space-x-4 text-sm text-slate-600">
                <Link className="hover:text-slate-900" href="/cases">
                  Cases
                </Link>
                <Link className="hover:text-slate-900" href="/login">
                  Login
                </Link>
                <Link className="hover:text-slate-900" href="/register">
                  Register
                </Link>
              </nav>
            </div>
          </header>
          <main className="flex-1">
            <div className="mx-auto max-w-5xl px-4 py-12">{children}</div>
          </main>
          <footer className="border-t border-slate-200 bg-white">
            <div className="mx-auto max-w-5xl px-4 py-6 text-xs text-slate-500">
              © {new Date().getFullYear()} ClaimVault Labs. Built with FastAPI + Next.js.
            </div>
          </footer>
        </div>
      </body>
    </html>
  );
}

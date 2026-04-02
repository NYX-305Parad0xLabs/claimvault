import "./globals.css";

export const metadata = {
  title: "ClaimVault",
  description: "Parad0x Labs custody and compliance claim center",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <main className="min-h-screen bg-slate-950 text-white">
          {children}
        </main>
      </body>
    </html>
  );
}

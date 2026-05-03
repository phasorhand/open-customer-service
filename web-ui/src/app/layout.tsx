import "./globals.css";
import type { Metadata } from "next";
import { Providers } from "./providers";
import { SidebarNav } from "@/components/sidebar-nav";

export const metadata: Metadata = {
  title: "OpenCS Admin",
  description: "Customer service agent admin console",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <Providers>
          <div className="grid grid-cols-[16rem_1fr] min-h-screen">
            <aside className="border-r bg-muted/20">
              <div className="h-14 flex items-center px-6 border-b">
                <span className="font-semibold">OpenCS</span>
              </div>
              <SidebarNav />
            </aside>
            <main className="p-6">{children}</main>
          </div>
        </Providers>
      </body>
    </html>
  );
}

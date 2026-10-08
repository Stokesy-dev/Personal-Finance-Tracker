import type { Metadata } from "next";
import "./styles.css";

export const metadata: Metadata = {
  title: "Personal Finance Tracker",
  description: "Understand your spending and build better financial habits.",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return <html lang="en"><body>{children}</body></html>;
}

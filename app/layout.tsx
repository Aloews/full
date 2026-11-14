import type { Metadata } from "next";
import "./globals.css";
export const metadata: Metadata = { title: "AUREL | Private Property", description: "Private real estate intelligence and services for exceptional property." };
export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) { return <html lang="en"><body>{children}</body></html>; }

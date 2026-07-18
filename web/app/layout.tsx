import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "youtube-clipper",
  description: "Clip and download sections of online videos as MP4, MP3 or GIF.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}

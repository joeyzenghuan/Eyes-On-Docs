import './globals.css';
import { Orbitron } from 'next/font/google'

const orbitron = Orbitron({ 
  subsets: ['latin'],
  weight: ['400', '700'],
  variable: '--font-orbitron'
})

export const metadata = {
  title: 'Eyes On Docs',
  description: 'Document Update Notification Platform',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en" className={`${orbitron.variable} dark bg-background-primary`}>
      <body className="bg-background-primary text-text-primary min-h-screen flex flex-col">{children}</body>
    </html>
  )
}

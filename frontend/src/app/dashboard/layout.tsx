import TitleBar from "@/components/TitleBar";

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="flex flex-col min-h-screen">
      <TitleBar />
      <main className="flex-1 overflow-auto bg-zinc-50 dark:bg-zinc-950">
        {children}
      </main>
    </div>
  );
}

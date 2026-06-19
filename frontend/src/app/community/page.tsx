import { Metadata } from "next";
import Header from "@/components/Header";
import Footer from "@/components/Footer";
import CommunityBoard from "@/components/CommunityBoard";

export const metadata: Metadata = {
  title: "Community | LinkdApply",
  description:
    "Read what job seekers say about LinkdApply and share your own feedback to help us improve.",
};

export default function CommunityPage() {
  return (
    <div className="flex grow flex-col bg-white text-zinc-900 selection:bg-accent/10">
      <Header />

      <main className="relative flex flex-col pt-32 pb-24 overflow-hidden min-h-[calc(100vh-100px)]">
        <div className="absolute top-0 left-0 w-full h-full grid-pattern pointer-events-none z-0 opacity-40" />
        <div className="absolute top-0 left-0 w-full h-full noise-texture pointer-events-none z-0" />
        <div className="absolute top-0 left-0 w-full h-[800px] natural-glow pointer-events-none z-0" />

        <div className="relative z-10 mx-auto w-full max-w-6xl px-6 space-y-20 animate-in fade-in slide-in-from-bottom-8 duration-700">
          <CommunityBoard />
        </div>
      </main>

      <Footer />
    </div>
  );
}

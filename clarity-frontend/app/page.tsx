import { Header } from "@/components/header";
import { MainContent } from "@/components/main-content";
import { Footer } from "@/components/footer";

export default function Home() {
  return (
    <div className="flex min-h-screen flex-col">
      <Header />
      <main className="flex-1 py-8">
        <MainContent />
      </main>
      <Footer />
    </div>
  );
}

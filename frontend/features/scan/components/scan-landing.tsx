import { ScanForm } from "./scan-form";
import { ScanPreview } from "./scan-preview";

export function ScanLanding() {
  return (
    <section className="flex min-h-[calc(100vh-80px)] flex-col items-center justify-center px-6 py-16">
      <div className="w-full max-w-6xl">
        <div className="grid items-center gap-20 lg:grid-cols-2">
          <ScanForm />
          <ScanPreview />
        </div>
      </div>
    </section>
  );
}

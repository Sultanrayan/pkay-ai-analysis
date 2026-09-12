import { Button, Card } from "../components/ui.jsx";

export default function NotFound() {
  return (
    <div className="mx-auto flex max-w-3xl flex-col items-center px-4 py-28 text-center sm:px-6">
      <p className="font-mono text-7xl font-extrabold text-gradient sm:text-9xl">
        404
      </p>
      <h1 className="mt-6 text-3xl font-bold text-white">
        This page left the chart
      </h1>
      <p className="mt-3 max-w-md text-neutral-400">
        The page you are looking for does not exist or has moved. Let's get you
        back to the analysis.
      </p>
      <div className="mt-8 flex flex-wrap justify-center gap-3">
        <Button to="/" size="lg">
          Back home
        </Button>
        <Button to="/docs" variant="secondary" size="lg">
          Browse docs
        </Button>
      </div>
      <Card className="mt-12 w-full">
        <p className="text-sm text-neutral-400">
          Looking for the API? Head to{" "}
          <span className="font-mono text-neutral-200">/docs#endpoint</span> or
          create a key in the{" "}
          <a href="/dashboard" className="text-white hover:underline">
            dashboard
          </a>
          .
        </p>
      </Card>
    </div>
  );
}

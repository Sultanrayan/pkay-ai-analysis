import { lazy, Suspense } from "react";
import { Route, Routes } from "react-router-dom";
import Layout from "./components/Layout.jsx";
import Home from "./pages/Home.jsx";

const HowItWorks = lazy(() => import("./pages/HowItWorks.jsx"));
const Features = lazy(() => import("./pages/Features.jsx"));
const Pricing = lazy(() => import("./pages/Pricing.jsx"));
const Docs = lazy(() => import("./pages/Docs.jsx"));
const Dashboard = lazy(() => import("./pages/Dashboard.jsx"));
const About = lazy(() => import("./pages/About.jsx"));
const Login = lazy(() => import("./pages/Login.jsx"));
const NotFound = lazy(() => import("./pages/NotFound.jsx"));

function PageLoader() {
  return (
    <div className="grid min-h-[60vh] place-items-center">
      <div className="flex items-center gap-3 text-neutral-400">
        <span className="h-5 w-5 animate-spin rounded-full border-2 border-white/20 border-t-white" />
        Loading…
      </div>
    </div>
  );
}

function SiteRoutes() {
  return (
    <Layout>
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/how-it-works" element={<HowItWorks />} />
        <Route path="/features" element={<Features />} />
        <Route path="/pricing" element={<Pricing />} />
        <Route path="/docs" element={<Docs />} />
        <Route path="/about" element={<About />} />
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Login />} />
        <Route path="*" element={<NotFound />} />
      </Routes>
    </Layout>
  );
}

export default function App() {
  return (
    <Suspense fallback={<PageLoader />}>
      <Routes>
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="*" element={<SiteRoutes />} />
      </Routes>
    </Suspense>
  );
}

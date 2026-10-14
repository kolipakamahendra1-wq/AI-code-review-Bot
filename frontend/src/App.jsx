import { Route, Routes } from "react-router-dom";
import Nav from "./components/Nav.jsx";
import Footer from "./components/Footer.jsx";
import Landing from "./pages/Landing.jsx";
import Playground from "./pages/Playground.jsx";
import Dashboard from "./pages/Dashboard.jsx";
import ReviewDetail from "./pages/ReviewDetail.jsx";
import Docs from "./pages/Docs.jsx";

export default function App() {
  return (
    <div className="flex min-h-dvh flex-col">
      <Nav />
      <main className="flex-1">
        <Routes>
          <Route path="/" element={<Landing />} />
          <Route path="/playground" element={<Playground />} />
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/reviews/:id" element={<ReviewDetail />} />
          <Route path="/docs" element={<Docs />} />
          <Route path="*" element={<Landing />} />
        </Routes>
      </main>
      <Footer />
    </div>
  );
}

import { useLocation, useNavigate } from "react-router-dom";
import { AuthBox } from "../components/auth.jsx";

export default function Login() {
  const navigate = useNavigate();
  const { pathname } = useLocation();
  const initialMode = pathname === "/register" ? "register" : "signin";

  return (
    <div className="flex min-h-[70vh] items-center justify-center px-4 py-16">
      <AuthBox
        initialMode={initialMode}
        onAuthenticated={() => navigate("/dashboard")}
      />
    </div>
  );
}

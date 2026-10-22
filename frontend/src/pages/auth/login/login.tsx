
import { useState, type FormEvent } from "react";
import { Link, useNavigate } from "react-router";
import { all_routes } from "../../../routes/all_routes";
import API, { BACKEND_URL } from "../../../services/api";
import soinLogo from "../../../../public/soinLogo.jpeg";
import soinBanner from "../../../../public/soinBanner.jpeg";

const route = all_routes;

const Login = () => {
  const navigate = useNavigate();

  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setError("");

    if (!username.trim() || !password.trim()) {
      setError("Please enter your username and password.");
      return;
    }

    setLoading(true);

    try {
      const res = await API.post(
        `${BACKEND_URL}/users/login/`,
        {
          username: username.trim(),
          password,
        }
      );

      if (res.data?.status === "success") {
        sessionStorage.setItem("user", JSON.stringify(res.data.user));
        navigate(res.data.redirect_to || route.dashboard);
      } else {
        setError(res.data?.message || "Login failed. Please try again.");
      }
    } catch (err: any) {
      const message =
        err?.response?.data?.message ||
        err?.response?.data?.detail ||
        "Invalid username or password.";

      setError(message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="acc-vh overflow-hidden">
      <div className="row vh-100 w-100 g-0">
        {/* Left: Login form */}
        <div className="col-lg-5 vh-100 overflow-y-auto overflow-x-hidden d-flex flex-column justify-content-between bg-white px-4 px-md-5 py-4">
          {/* Local logo */}
          <div className="text-center pt-2 pb-4">
            <img
              src={soinLogo}
              alt="Soin Logo"
              className="img-fluid"
              style={{
                width: 100,
                height: 100,
                marginTop: 30,
                borderRadius: "50%",
                objectFit: "cover",
              }}
            />
          </div>

          {/* Form */}
          <div className="w-100" style={{ maxWidth: 400, margin: "0 auto" }}>
            <div className="mb-4">
              <h3 className="mb-1 fw-bold text-dark">Welcome</h3>
              <p className="text-muted fs-13 mb-0">
                Sign in to your account to continue.
              </p>
            </div>

            {error && (
              <div
                className="alert alert-danger d-flex align-items-center gap-2 fs-13 py-2 mb-3"
                role="alert"
              >
                <i className="ti ti-circle-x fs-5 flex-shrink-0" />
                <span>{error}</span>
              </div>
            )}

            <form
              onSubmit={handleSubmit}
              action="/auth/login/"
              autoComplete="on"
            >
              {/* Username */}
              <div className="mb-3">
                <label htmlFor="username" className="form-label fw-medium">
                  Username
                </label>

                <div className="input-group input-group-flat">
                  <input
                    id="username"
                    name="username"
                    type="text"
                    className="form-control"
                    placeholder="Enter your username"
                    value={username}
                    onChange={(e) => setUsername(e.target.value)}
                    autoComplete="username"
                    required
                    disabled={loading}
                  />

                  <span className="input-group-text">
                    <i className="ti ti-user text-muted" />
                  </span>
                </div>
              </div>

              {/* Password */}
              <div className="mb-4">
                <label htmlFor="password" className="form-label fw-medium">
                  Password
                </label>

                <div className="input-group input-group-flat pass-group">
                  <input
                    id="password"
                    name="password"
                    type={showPassword ? "text" : "password"}
                    className="form-control pass-input"
                    placeholder="Enter your password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    autoComplete="current-password"
                    required
                    disabled={loading}
                  />

                  <button
                    type="button"
                    className="input-group-text"
                    aria-label={showPassword ? "Hide password" : "Show password"}
                    onClick={() => setShowPassword((current) => !current)}
                    disabled={loading}
                    style={{ cursor: "pointer" }}
                  >
                    <i
                      className={`ti ${
                        showPassword ? "ti-eye" : "ti-eye-off"
                      }`}
                    />
                  </button>
                </div>
              </div>

              {/* Submit */}
              <button
                type="submit"
                className="btn btn-primary w-100 d-flex align-items-center justify-content-center gap-2 py-2"
                disabled={loading}
              >
                {loading && (
                  <span className="spinner-border spinner-border-sm" />
                )}

                <i className="ti ti-login" />
                {loading ? "Signing in..." : "Sign In"}
              </button>
              
<div className="text-center mt-4">
  <p className="text-muted fs-13 mb-0">
    Don't have an account?{" "}
    <Link
      to={route.register}
      className="fw-semibold text-primary text-decoration-none"
    >
      Sign up
    </Link>
  </p>
</div>

            </form>
          </div>

          {/* Footer */}
          <div className="text-center text-muted fs-12 pb-2">
            Soinvet © {new Date().getFullYear()} All rights reserved.
          </div>
        </div>

        {/* Right: Local banner image */}
        <div className="col-lg-7 d-none d-lg-block position-relative overflow-hidden">
          <img
            src={soinBanner}
            alt="Soinvet"
            className="w-100 h-100"
            style={{
              objectFit: "cover",
              objectPosition: "center",
            }}
          />

          <div
            className="position-absolute top-0 start-0 w-100 h-100"
            style={{ background: "rgba(0,0,0,0.18)" }}
          />
        </div>
      </div>
    </div>
  );
};

export default Login;

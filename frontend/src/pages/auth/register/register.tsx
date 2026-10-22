
import { Link, useNavigate } from "react-router";
import { useEffect, useState } from "react";
import type { ChangeEvent, FormEvent } from "react";
import { all_routes } from "../../../routes/all_routes";
import { BACKEND_URL } from "../../../services/api";
import soinLogo from "../../../../public/soinLogo.jpeg";
import soinBanner from "../../../../public/soinBanner.jpeg";

type PasswordField = "password" | "confirmPassword";

type Role = { id: number; name: string };

type FieldDef = {
  name: string;
  label: string;
  placeholder?: string;
  required?: boolean;
};

// Backend URLs
const DJANGO_ORIGIN = String(BACKEND_URL ?? "")
  .replace(/\/+$/, "")
  .replace(/\/api$/, "");

const REGISTER_URL = `${DJANGO_ORIGIN}/users/register/`;
const CSRF_URL = `${DJANGO_ORIGIN}/users/csrf/`;

const readCookie = (name: string): string => {
  const match = document.cookie
    .split("; ")
    .find((row) => row.startsWith(`${name}=`));

  return match ? decodeURIComponent(match.split("=")[1]) : "";
};

const parseResponse = async (res: Response) => {
  const text = await res.text();

  try {
    return { json: JSON.parse(text), raw: text };
  } catch {
    return { json: null, raw: text };
  }
};

const describeError = (
  res: Response,
  json: any,
  fallback: string
): string => {
  if (json?.message) return json.message;

  if (json?.detail) {
    return `${json.detail} (${res.status} from ${res.url})`;
  }

  return `${fallback} (${res.status} from ${res.url})`;
};

const COUNTY_FIELDS: FieldDef[] = [
  { name: "county", label: "County", required: true },
  { name: "subcounty", label: "Sub-county" },
  { name: "location", label: "Location / Ward" },
];

const ROLE_FIELDS: Record<string, FieldDef[]> = {
  farmer: [
    { name: "farm_name", label: "Farm Name", placeholder: "e.g. Soin Farm" },
    ...COUNTY_FIELDS,
  ],
  "vet officer": [
    {
      name: "specialization",
      label: "Specialization",
      placeholder: "e.g. Large animals",
    },
    { name: "vet_category", label: "Vet Category" },
    {
      name: "registration_number",
      label: "KVB Registration No.",
      required: true,
    },
    { name: "licence_number", label: "Licence Number", required: true },
    { name: "supervisor", label: "Supervisor" },
    { name: "business_name", label: "Practice / Business Name" },
    ...COUNTY_FIELDS,
  ],
  agrovet: [
    { name: "agrovet_name", label: "Agrovet Name", required: true },
    { name: "vmd_number", label: "VMD Number", required: true },
    { name: "licence_number", label: "Licence Number" },
    { name: "town", label: "Town" },
    ...COUNTY_FIELDS,
  ],
  cooperative: [
    { name: "cooperative_name", label: "Cooperative Name", required: true },
    { name: "registration_number", label: "Registration Number" },
    ...COUNTY_FIELDS,
  ],
  slaughterhouse: [
    {
      name: "business_name",
      label: "Slaughterhouse Name",
      required: true,
    },
    { name: "licence_number", label: "Licence Number", required: true },
    ...COUNTY_FIELDS,
  ],
};

const initialForm: Record<string, string> = {
  firstname: "",
  lastname: "",
  username: "",
  email: "",
  phone: "",
  role: "",
  password: "",
  password2: "",
};

const Register = () => {
  const navigate = useNavigate();

  const [passwordVisibility, setPasswordVisibility] = useState({
    password: false,
    confirmPassword: false,
  });

  const [roles, setRoles] = useState<Role[]>([]);
  const [form, setForm] = useState<Record<string, string>>(initialForm);
  const [agreed, setAgreed] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  const togglePasswordVisibility = (field: PasswordField) => {
    setPasswordVisibility((previous) => ({
      ...previous,
      [field]: !previous[field],
    }));
  };

  // Load available roles.
  useEffect(() => {
    const loadRoles = async () => {
      try {
        const res = await fetch(REGISTER_URL, {
          method: "GET",
          credentials: "include",
          headers: { Accept: "application/json" },
        });

        const { json } = await parseResponse(res);

        if (res.ok && json?.status === "success") {
          setRoles(json.roles ?? []);
        } else {
          setError(
            describeError(res, json, "Could not load account types")
          );
        }
      } catch {
        setError(
          `Could not reach the server at ${REGISTER_URL}. Is Django running?`
        );
      }
    };

    loadRoles();
  }, []);

  const selectedRole = roles.find(
    (role) => String(role.id) === form.role
  );

  const roleKey = selectedRole?.name.trim().toLowerCase() ?? "";
  const roleFields = ROLE_FIELDS[roleKey] ?? [];

  const handleChange = (
    e: ChangeEvent<HTMLInputElement | HTMLSelectElement>
  ) => {
    const { name, value } = e.target;

    setForm((previous) => ({
      ...previous,
      [name]: value,
    }));
  };

  // Changing role clears previously entered role-specific fields.
  const handleRoleChange = (e: ChangeEvent<HTMLSelectElement>) => {
    setForm({
      ...initialForm,
      role: e.target.value,
    });
  };

  const getCsrfToken = async (): Promise<string> => {
    let token = readCookie("csrftoken");

    if (!token) {
      const res = await fetch(CSRF_URL, {
        credentials: "include",
        headers: { Accept: "application/json" },
      });

      const { json } = await parseResponse(res);
      token = json?.csrftoken ?? readCookie("csrftoken");
    }

    return token;
  };

  const handleSubmit = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setError(null);
    setSuccess(null);

    if (!form.role) {
      setError("Please choose an account type.");
      return;
    }

    if (form.password !== form.password2) {
      setError("Passwords do not match.");
      return;
    }

    if (!agreed) {
      setError("You must agree to the Terms & Privacy policy.");
      return;
    }

    setLoading(true);

    try {
      const csrfToken = await getCsrfToken();

      const res = await fetch(REGISTER_URL, {
        method: "POST",
        credentials: "include",
        headers: {
          "Content-Type": "application/json",
          Accept: "application/json",
          "X-CSRFToken": csrfToken,
        },
        body: JSON.stringify(form),
      });

      const { json } = await parseResponse(res);

      if (res.ok && json?.status === "success") {
        setSuccess(json.message || "Account created successfully.");

        window.setTimeout(() => {
          navigate(all_routes.login);
        }, 1500);
      } else {
        setError(describeError(res, json, "Registration failed"));
      }
    } catch {
      setError(
        `Could not reach the server at ${REGISTER_URL}. Is Django running?`
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="acc-vh overflow-hidden">
      <div className="row vh-100 w-100 g-0">
        {/* Left: Registration form */}
        <div className="col-lg-6 vh-100 overflow-y-auto overflow-x-hidden bg-white">
          <div className="row h-100">
            <div className="col-md-10 mx-auto">
              <form
                className="d-flex justify-content-between flex-column p-4 pb-0 min-vh-100"
                onSubmit={handleSubmit}
                autoComplete="on"
              >
                {/* Local logo */}
                <div className="text-center pt-2 pb-4">
                  <img
                    src={soinLogo}
                    alt="Super POS Logo"
                    className="img-fluid"
                    style={{
                      width: 100,
                      height: 100,
                      marginTop: 20,
                      borderRadius: "50%",
                      objectFit: "cover",
                    }}
                  />
                </div>

                <div>
                  <div className="mb-3">
                    <h3 className="mb-2 fw-bold">Create your account</h3>
                    <p className="text-muted mb-0">
                      Register to get started with Super POS.
                    </p>
                  </div>

                  {error && (
                    <div className="alert alert-danger py-2" role="alert">
                      <i className="ti ti-alert-circle me-2" />
                      {error}
                    </div>
                  )}

                  {success && (
                    <div className="alert alert-success py-2" role="status">
                      <i className="ti ti-circle-check me-2" />
                      {success}
                    </div>
                  )}

                  {/* Account type */}
                  <div className="mb-3">
                    <label htmlFor="role" className="form-label">
                      Register as <span className="text-danger">*</span>
                    </label>

                    <select
                      id="role"
                      name="role"
                      className="form-select"
                      value={form.role}
                      onChange={handleRoleChange}
                      required
                      disabled={loading}
                    >
                      <option value="">Select account type</option>

                      {roles.map((role) => (
                        <option key={role.id} value={role.id}>
                          {role.name}
                        </option>
                      ))}
                    </select>
                  </div>

                  {/* Basic details */}
                  <div className="row">
                    <div className="col-md-6 mb-3">
                      <label htmlFor="firstname" className="form-label">
                        First Name
                      </label>
                      <input
                        id="firstname"
                        type="text"
                        name="firstname"
                        className="form-control"
                        value={form.firstname}
                        onChange={handleChange}
                        autoComplete="given-name"
                        required
                        disabled={loading}
                      />
                    </div>

                    <div className="col-md-6 mb-3">
                      <label htmlFor="lastname" className="form-label">
                        Last Name
                      </label>
                      <input
                        id="lastname"
                        type="text"
                        name="lastname"
                        className="form-control"
                        value={form.lastname}
                        onChange={handleChange}
                        autoComplete="family-name"
                        required
                        disabled={loading}
                      />
                    </div>
                  </div>

                  {/* Username */}
                  <div className="mb-3">
                    <label htmlFor="username" className="form-label">
                      Username
                    </label>

                    <div className="input-group input-group-flat">
                      <input
                        id="username"
                        type="text"
                        name="username"
                        className="form-control"
                        value={form.username}
                        onChange={handleChange}
                        autoComplete="username"
                        required
                        disabled={loading}
                      />
                      <span className="input-group-text">
                        <i className="ti ti-user" />
                      </span>
                    </div>
                  </div>

                  {/* Email */}
                  <div className="mb-3">
                    <label htmlFor="email" className="form-label">
                      Email Address
                    </label>

                    <div className="input-group input-group-flat">
                      <input
                        id="email"
                        type="email"
                        name="email"
                        className="form-control"
                        value={form.email}
                        onChange={handleChange}
                        autoComplete="email"
                        required
                        disabled={loading}
                      />
                      <span className="input-group-text">
                        <i className="ti ti-mail" />
                      </span>
                    </div>
                  </div>

                  {/* Phone */}
                  <div className="mb-3">
                    <label htmlFor="phone" className="form-label">
                      Phone Number
                    </label>

                    <div className="input-group input-group-flat">
                      <input
                        id="phone"
                        type="tel"
                        name="phone"
                        className="form-control"
                        placeholder="07XXXXXXXX"
                        value={form.phone}
                        onChange={handleChange}
                        autoComplete="tel"
                        required
                        disabled={loading}
                      />
                      <span className="input-group-text">
                        <i className="ti ti-phone" />
                      </span>
                    </div>
                  </div>

                  {/* Role-specific fields */}
                  {roleFields.length > 0 && (
                    <div className="border rounded p-3 mb-3">
                      <h6 className="mb-3">
                        {selectedRole?.name} details
                      </h6>

                      <div className="row">
                        {roleFields.map((field) => (
                          <div
                            className="col-md-6 mb-3"
                            key={field.name}
                          >
                            <label
                              htmlFor={field.name}
                              className="form-label"
                            >
                              {field.label}
                              {field.required && (
                                <span className="text-danger"> *</span>
                              )}
                            </label>

                            <input
                              id={field.name}
                              type="text"
                              name={field.name}
                              className="form-control"
                              placeholder={field.placeholder}
                              value={form[field.name] ?? ""}
                              onChange={handleChange}
                              required={field.required}
                              disabled={loading}
                            />
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Password */}
                  <div className="mb-3">
                    <label htmlFor="password" className="form-label">
                      Password
                    </label>

                    <div className="input-group input-group-flat pass-group">
                      <input
                        id="password"
                        type={passwordVisibility.password ? "text" : "password"}
                        name="password"
                        className="form-control pass-input"
                        placeholder="Enter your password"
                        value={form.password}
                        onChange={handleChange}
                        autoComplete="new-password"
                        required
                        disabled={loading}
                      />

                      <button
                        type="button"
                        className="input-group-text"
                        aria-label={
                          passwordVisibility.password
                            ? "Hide password"
                            : "Show password"
                        }
                        onClick={() => togglePasswordVisibility("password")}
                        disabled={loading}
                        style={{ cursor: "pointer" }}
                      >
                        <i
                          className={`ti ${
                            passwordVisibility.password
                              ? "ti-eye"
                              : "ti-eye-off"
                          }`}
                        />
                      </button>
                    </div>
                  </div>

                  {/* Confirm password */}
                  <div className="mb-3">
                    <label htmlFor="password2" className="form-label">
                      Confirm Password
                    </label>

                    <div className="input-group input-group-flat pass-group">
                      <input
                        id="password2"
                        type={
                          passwordVisibility.confirmPassword
                            ? "text"
                            : "password"
                        }
                        name="password2"
                        className="form-control pass-input"
                        placeholder="Confirm your password"
                        value={form.password2}
                        onChange={handleChange}
                        autoComplete="new-password"
                        required
                        disabled={loading}
                      />

                      <button
                        type="button"
                        className="input-group-text"
                        aria-label={
                          passwordVisibility.confirmPassword
                            ? "Hide confirm password"
                            : "Show confirm password"
                        }
                        onClick={() =>
                          togglePasswordVisibility("confirmPassword")
                        }
                        disabled={loading}
                        style={{ cursor: "pointer" }}
                      >
                        <i
                          className={`ti ${
                            passwordVisibility.confirmPassword
                              ? "ti-eye"
                              : "ti-eye-off"
                          }`}
                        />
                      </button>
                    </div>
                  </div>

                  {/* Terms */}
                  <div className="d-flex align-items-center mb-3">
                    <div className="form-check form-check-md d-flex align-items-center">
                      <input
                        className="form-check-input mt-0"
                        type="checkbox"
                        id="terms"
                        checked={agreed}
                        onChange={(e) => setAgreed(e.target.checked)}
                        required
                        disabled={loading}
                      />

                      <label
                        className="form-check-label ms-2"
                        htmlFor="terms"
                      >
                        I agree to the{" "}
                        <Link to="#" className="text-primary link-hover">
                          Terms &amp; Privacy
                        </Link>
                      </label>
                    </div>
                  </div>

                  {/* Submit */}
                  <div className="mb-3">
                    <button
                      type="submit"
                      className="btn btn-primary w-100 d-flex align-items-center justify-content-center gap-2"
                      disabled={loading}
                    >
                      {loading ? (
                        <>
                          <span className="spinner-border spinner-border-sm" />
                          Creating account...
                        </>
                      ) : (
                        <>
                          <i className="ti ti-user-plus" />
                          Sign Up
                        </>
                      )}
                    </button>
                  </div>

                  <div className="mb-3 text-center">
                    <p className="mb-0">
                      Already have an account?{" "}
                      <Link
                        to={all_routes.login}
                        className="link-indigo fw-bold link-hover"
                      >
                        Sign In Instead
                      </Link>
                    </p>
                  </div>
                </div>

                {/* Footer */}
                <div className="text-center text-muted fs-12 pb-4">
                  Super POS. © {new Date().getFullYear()} All rights reserved.
                </div>
              </form>
            </div>
          </div>
        </div>

        {/* Right: Local banner image */}
        <div className="col-lg-6 d-none d-lg-block position-relative overflow-hidden">
          <img
            src={soinBanner}
            alt="Super POS"
            className="w-100 h-100 position-absolute top-0 start-0"
            style={{
              objectFit: "cover",
              objectPosition: "center",
            }}
          />

          <div
            className="position-absolute top-0 start-0 w-100 h-100"
            style={{ background: "rgba(0, 0, 0, 0.18)" }}
          />
        </div>
      </div>
    </div>
  );
};

export default Register;

import { useEffect, useState, useCallback } from "react";
import {
  getUsers, createUser, updateUser, deleteUser,
  resetUserPassword, toggleUserStatus, getUserFormData,
} from "../../../../services/userService";
import { toast, confirm } from "../../../../utils/toast";

const EMPTY_FORM = {
  username: "", firstname: "", lastname: "", email: "",
  phone: "", password: "", role: "", endpoint: "",
};

function Avatar({ user }: { user: any }) {
  const letter = (user.firstname?.[0] || user.username?.[0] || "?").toUpperCase();
  return (
    <div className="avatar avatar-md rounded-circle bg-primary d-flex align-items-center justify-content-center flex-shrink-0"
      style={{ width: 40, height: 40 }}>
      <span className="fw-bold text-white fs-14">{letter}</span>
    </div>
  );
}

export default function Users() {
  const [data, setData] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [roleFilter, setRoleFilter] = useState("all");

  const [formMeta, setFormMeta] = useState<{ roles: any[]; endpoints: any[] }>({ roles: [], endpoints: [] });
  const [form, setForm] = useState<any>(EMPTY_FORM);
  const [editId, setEditId] = useState<number | null>(null);
  const [saving, setSaving] = useState(false);
  const [formError, setFormError] = useState("");

  const [selectedUser, setSelectedUser] = useState<any>(null);
  const [deleteTarget, setDeleteTarget] = useState<any>(null);

  const fetchUsers = useCallback(async () => {
    setLoading(true);
    try {
      const result = await getUsers();
      setData(result);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchUsers();
    getUserFormData()
      .then(d => setFormMeta({ roles: d?.roles || [], endpoints: d?.endpoints || [] }))
      .catch(console.error);
  }, [fetchUsers]);

  // ── filtering ──────────────────────────────────────────────────────────────
  const roles = Array.from(new Set(data.map((u) => u.role?.role_name).filter(Boolean)));
  const filtered = data.filter((u) => {
    const q = search.toLowerCase();
    const matchSearch =
      !q ||
      `${u.firstname} ${u.lastname}`.toLowerCase().includes(q) ||
      (u.username || "").toLowerCase().includes(q) ||
      (u.email || "").toLowerCase().includes(q) ||
      (u.phone || "").includes(q);
    const matchRole = roleFilter === "all" || u.role?.role_name === roleFilter;
    return matchSearch && matchRole;
  });

  // ── offcanvas helpers ──────────────────────────────────────────────────────
  const showOffcanvas = (id: string) => {
    const el = document.getElementById(id);
    if (el) (window as any).bootstrap?.Offcanvas?.getOrCreateInstance(el)?.show();
  };
  const hideOffcanvas = (id: string) => {
    const el = document.getElementById(id);
    if (el) (window as any).bootstrap?.Offcanvas?.getInstance(el)?.hide();
  };
  const showModal = (id: string) => {
    const el = document.getElementById(id);
    if (el) (window as any).bootstrap?.Modal?.getOrCreateInstance(el)?.show();
  };
  const hideModal = (id: string) => {
    const el = document.getElementById(id);
    if (el) (window as any).bootstrap?.Modal?.getInstance(el)?.hide();
  };

  // ── create ─────────────────────────────────────────────────────────────────
  const handleCreate = () => {
    setEditId(null);
    setForm(EMPTY_FORM);
    setFormError("");
    showOffcanvas("offcanvas_user_form");
  };

  // ── edit ───────────────────────────────────────────────────────────────────
  const handleEdit = (u: any, e?: React.MouseEvent) => {
    e?.stopPropagation();
    setEditId(u.id);
    setForm({
      username: u.username || "",
      firstname: u.firstname || "",
      lastname: u.lastname || "",
      email: u.email || "",
      phone: u.phone || "",
      password: "",
      role: u.role?.id || "",
      endpoint: u.endpoint?.id || "",
    });
    setFormError("");
    showOffcanvas("offcanvas_user_form");
  };

  // ── save ───────────────────────────────────────────────────────────────────
  const handleSave = async () => {
    setSaving(true);
    setFormError("");
    try {
      const payload: any = { ...form };
      if (!payload.password) delete payload.password;
      if (editId) {
        const updated = await updateUser(editId, payload);
        // refresh selected user if it's the one being edited
        if (selectedUser?.id === editId) setSelectedUser(updated);
      } else {
        await createUser(payload);
      }
      hideOffcanvas("offcanvas_user_form");
      fetchUsers();
    } catch (e: any) {
      const data = e?.response?.data;
      const msg = data?.error || data?.detail || (typeof data === 'string' ? data : null) || "Save failed. Check all fields.";
      setFormError(msg);
    } finally {
      setSaving(false);
    }
  };

  // ── delete ─────────────────────────────────────────────────────────────────
  const handleDeleteConfirm = async () => {
    if (!deleteTarget) return;
    try {
      await deleteUser(deleteTarget.id);
      hideModal("modal_delete_user");
      if (selectedUser?.id === deleteTarget.id) setSelectedUser(null);
      fetchUsers();
    } catch (e) {
      console.error(e);
    }
  };

  // ── reset password ─────────────────────────────────────────────────────────
  const handleResetPassword = async (u: any, e?: React.MouseEvent) => {
    e?.stopPropagation();
    const ok = await confirm(`Reset password for ${u.firstname} ${u.lastname} to their username?`, {
      title: 'Reset Password', confirmText: 'Reset', icon: 'warning',
    });
    if (!ok) return;
    try {
      await resetUserPassword(u.id);
      toast.success("Password reset successfully.");
    } catch {
      toast.error("Failed to reset password.");
    }
  };

  // ── toggle status ──────────────────────────────────────────────────────────
  const handleToggleStatus = async (u: any, e?: React.MouseEvent) => {
    e?.stopPropagation();
    const action = u.is_active ? "disable" : "enable";
    const ok = await confirm(`${action.charAt(0).toUpperCase() + action.slice(1)} ${u.firstname} ${u.lastname}?`, {
      title: `${action.charAt(0).toUpperCase() + action.slice(1)} User`,
      confirmText: action.charAt(0).toUpperCase() + action.slice(1),
      icon: 'warning',
    });
    if (!ok) return;
    try {
      const result = await toggleUserStatus(u.id);
      if (selectedUser?.id === u.id) setSelectedUser({ ...selectedUser, is_active: result.is_active });
      fetchUsers();
    } catch {
      toast.error("Failed to update status.");
    }
  };

  // initialize Bootstrap tooltips whenever offcanvas form opens
  useEffect(() => {
    const timer = setTimeout(() => {
      document.querySelectorAll('[data-bs-toggle="tooltip"]').forEach(el => {
        (window as any).bootstrap?.Tooltip?.getOrCreateInstance(el);
      });
    }, 300);
    return () => clearTimeout(timer);
  }, [editId, saving]);

  return (
    <>
      <div className="page-wrapper">
        <div className="content">

          {/* Header */}
          <div className="d-flex align-items-center justify-content-between mb-3 flex-wrap gap-2">
            <div>
              <h4 className="fw-semibold mb-1">User Management</h4>
              <p className="text-muted fs-13 mb-0">{data.length} users in the system</p>
            </div>
            <button className="btn btn-primary" onClick={handleCreate}>
              <i className="ti ti-plus me-1" /> Add User
            </button>
          </div>

          {/* Stats */}
          {!loading && data.length > 0 && (
            <div className="row g-3 mb-4">
              {[
                { label: "Total Users",   value: data.length,                              color: "text-primary",  bg: "bg-primary-gradient-100",  icon: "ti-users"       },
                { label: "Active",        value: data.filter(u => u.is_active).length,     color: "text-success",  bg: "bg-success-gradient-100",  icon: "ti-user-check"  },
                { label: "Inactive",      value: data.filter(u => !u.is_active).length,    color: "text-danger",   bg: "bg-danger-gradient-100",   icon: "ti-user-off"    },
                { label: "Admins",        value: data.filter(u => u.is_admin).length,      color: "text-warning",  bg: "bg-warning-gradient-100",  icon: "ti-shield"      },
              ].map(s => (
                <div key={s.label} className="col-6 col-sm-3">
                  <div className="card mb-0 border shadow-none">
                    <div className="card-body p-3 position-relative">
                      <p className="fw-medium mb-1 fs-13">{s.label}</p>
                      <h4 className={`mb-0 ${s.color}`}>{s.value}</h4>
                      <div className={`avatar avatar-rounded avatar-sm ${s.bg} position-absolute top-0 end-0 m-2 d-flex align-items-center justify-content-center`}>
                        <i className={`ti ${s.icon} fs-5 ${s.color}`} />
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* Table card */}
          <div className="card border shadow-none">
            <div className="card-header border-bottom py-3 d-flex align-items-center justify-content-between flex-wrap gap-2">
              <div className="input-group input-group-flat" style={{ maxWidth: 260 }}>
                <span className="input-group-text bg-transparent border-end-0">
                  <i className="ti ti-search text-muted" />
                </span>
                <input type="text" className="form-control border-start-0 ps-1 fs-13"
                  placeholder="Search name, email, phone…"
                  value={search} onChange={e => setSearch(e.target.value)} />
                {search && (
                  <button className="btn btn-sm btn-link text-muted px-2" onClick={() => setSearch("")}>
                    <i className="ti ti-x" />
                  </button>
                )}
              </div>
              <div className="d-flex gap-2 align-items-center flex-wrap">
                <select className="form-select form-select-sm fs-13 w-auto" value={roleFilter}
                  onChange={e => setRoleFilter(e.target.value)}>
                  <option value="all">All Roles</option>
                  {roles.map(r => <option key={r} value={r}>{r}</option>)}
                </select>
                <button className="btn btn-sm btn-outline-secondary" onClick={fetchUsers}>
                  <i className="ti ti-refresh" />
                </button>
              </div>
            </div>

            <div className="card-body p-0">
              {loading ? (
                <div className="d-flex align-items-center justify-content-center py-5 text-muted">
                  <span className="spinner-border spinner-border-sm me-2" />Loading users…
                </div>
              ) : filtered.length === 0 ? (
                <div className="d-flex flex-column align-items-center justify-content-center py-5 text-muted">
                  <i className="ti ti-users-off fs-1 mb-2" />
                  <p className="fs-14 mb-0">No users found.</p>
                </div>
              ) : (
                <div className="table-responsive">
                  <table className="table table-hover mb-0 fs-13">
                    <thead className="table-light">
                      <tr>
                        <th className="ps-3">User</th>
                        <th>Username</th>
                        <th>Email</th>
                        <th>Phone</th>
                        <th>Role</th>
                        <th>Extension</th>
                        <th>Status</th>
                        <th className="text-end pe-3">Actions</th>
                      </tr>
                    </thead>
                    <tbody>
                      {filtered.map(u => (
                        <tr key={u.id} style={{ cursor: "pointer" }}
                          onClick={() => { setSelectedUser(u); showOffcanvas("offcanvas_user_profile"); }}>
                          <td className="ps-3">
                            <div className="d-flex align-items-center gap-2">
                              <Avatar user={u} />
                              <div>
                                <p className="fw-medium mb-0">{u.firstname} {u.lastname}</p>
                                <span className="text-muted fs-12">{u.role?.role_name || "—"}</span>
                              </div>
                            </div>
                          </td>
                          <td className="text-muted">{u.username}</td>
                          <td>{u.email || "—"}</td>
                          <td>{u.phone || "—"}</td>
                          <td>
                            <span className="badge bg-soft-primary text-primary">
                              {u.role?.role_name || "—"}
                            </span>
                          </td>
                          <td>{u.endpoint?.id || "—"}</td>
                          <td>
                            <span className={`badge ${u.is_active ? "bg-success-transparent text-success" : "bg-danger-transparent text-danger"}`}>
                              {u.is_active ? "Active" : "Inactive"}
                            </span>
                          </td>
                          <td className="text-end pe-3" onClick={e => e.stopPropagation()}>
                            <div className="dropdown">
                              <button type="button"
                                className="btn btn-sm btn-outline-light shadow-sm"
                                data-bs-toggle="dropdown" aria-expanded="false">
                                <i className="ti ti-dots-vertical" />
                              </button>
                              <ul className="dropdown-menu dropdown-menu-end">
                                <li>
                                  <button type="button" className="dropdown-item"
                                    onClick={() => { setSelectedUser(u); showOffcanvas("offcanvas_user_profile"); }}>
                                    <i className="ti ti-eye me-2 text-info" />View Profile
                                  </button>
                                </li>
                                <li>
                                  <button type="button" className="dropdown-item"
                                    onClick={(e) => handleEdit(u, e)}>
                                    <i className="ti ti-edit me-2 text-primary" />Edit
                                  </button>
                                </li>
                                <li>
                                  <button type="button" className="dropdown-item"
                                    onClick={(e) => handleResetPassword(u, e)}>
                                    <i className="ti ti-key me-2 text-warning" />Reset Password
                                  </button>
                                </li>
                                <li>
                                  <button type="button" className="dropdown-item"
                                    onClick={(e) => handleToggleStatus(u, e)}>
                                    <i className={`ti ${u.is_active ? "ti-user-off text-danger" : "ti-user-check text-success"} me-2`} />
                                    {u.is_active ? "Disable" : "Enable"}
                                  </button>
                                </li>
                                <li><hr className="dropdown-divider" /></li>
                                <li>
                                  <button type="button" className="dropdown-item text-danger"
                                    onClick={(e) => { e.stopPropagation(); setDeleteTarget(u); showModal("modal_delete_user"); }}>
                                    <i className="ti ti-trash me-2" />Delete
                                  </button>
                                </li>
                              </ul>
                            </div>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>

            {!loading && (
              <div className="card-footer border-top py-2 px-3 fs-12 text-muted">
                Showing <strong>{filtered.length}</strong> of <strong>{data.length}</strong> users
              </div>
            )}
          </div>
        </div>
      </div>

      {/* ── User Profile Offcanvas ─────────────────────────────────────────── */}
      <div className="offcanvas offcanvas-end" style={{ width: 420 }} tabIndex={-1} id="offcanvas_user_profile">
        <div className="offcanvas-header border-bottom">
          <h5 className="mb-0">User Profile</h5>
          <button type="button" className="btn-close" data-bs-dismiss="offcanvas" />
        </div>
        {selectedUser && (
          <div className="offcanvas-body p-0">
            {/* Profile header */}
            <div className="p-4 border-bottom text-center bg-light">
              <div className="avatar avatar-xl rounded-circle bg-primary d-flex align-items-center justify-content-center mx-auto mb-3"
                style={{ width: 72, height: 72 }}>
                <span className="fw-bold text-white fs-24">
                  {(selectedUser.firstname?.[0] || selectedUser.username?.[0] || "?").toUpperCase()}
                </span>
              </div>
              <h5 className="mb-1">{selectedUser.firstname} {selectedUser.lastname}</h5>
              <span className="badge bg-soft-primary text-primary mb-2">{selectedUser.role?.role_name || "—"}</span>
              <div className="mt-1">
                <span className={`badge ${selectedUser.is_active ? "bg-success-transparent text-success" : "bg-danger-transparent text-danger"}`}>
                  {selectedUser.is_active ? "Active" : "Inactive"}
                </span>
                {selectedUser.is_admin && <span className="badge bg-warning-transparent text-warning ms-1">Admin</span>}
              </div>
            </div>

            {/* Details */}
            <div className="p-4">
              {[
                { label: "Username",  value: selectedUser.username,       icon: "ti-user"         },
                { label: "Email",     value: selectedUser.email,          icon: "ti-mail"         },
                { label: "Phone",     value: selectedUser.phone || "—",   icon: "ti-phone"        },
                { label: "Extension", value: selectedUser.endpoint?.id || "—", icon: "ti-headset" },
                { label: "Joined",    value: selectedUser.date_joined ? new Date(selectedUser.date_joined).toLocaleDateString("en-GB", { day: "2-digit", month: "short", year: "numeric" }) : "—", icon: "ti-calendar" },
              ].map(item => (
                <div key={item.label} className="d-flex align-items-center gap-3 mb-3">
                  <div className="avatar avatar-sm rounded bg-light d-flex align-items-center justify-content-center flex-shrink-0">
                    <i className={`ti ${item.icon} text-muted`} />
                  </div>
                  <div>
                    <p className="text-muted fs-12 mb-0">{item.label}</p>
                    <p className="fw-medium mb-0 fs-14">{item.value}</p>
                  </div>
                </div>
              ))}
            </div>

            {/* Actions */}
            <div className="p-4 border-top d-flex flex-column gap-2">
              <button type="button" className="btn btn-primary w-100"
                onClick={() => { hideOffcanvas("offcanvas_user_profile"); handleEdit(selectedUser); }}>
                <i className="ti ti-edit me-2" />Edit User
              </button>
              <button type="button"
                className={`btn w-100 ${selectedUser.is_active ? "btn-outline-danger" : "btn-outline-success"}`}
                onClick={(e) => handleToggleStatus(selectedUser, e)}>
                <i className={`ti ${selectedUser.is_active ? "ti-user-off" : "ti-user-check"} me-2`} />
                {selectedUser.is_active ? "Disable Account" : "Enable Account"}
              </button>
              <button type="button" className="btn btn-outline-warning w-100"
                onClick={(e) => handleResetPassword(selectedUser, e)}>
                <i className="ti ti-key me-2" />Reset Password
              </button>
              <button type="button" className="btn btn-outline-danger w-100"
                onClick={(e) => { e.stopPropagation(); setDeleteTarget(selectedUser); hideOffcanvas("offcanvas_user_profile"); showModal("modal_delete_user"); }}>
                <i className="ti ti-trash me-2" />Delete User
              </button>
            </div>
          </div>
        )}
      </div>

      {/* ── Create / Edit Offcanvas ────────────────────────────────────────── */}
      <div className="offcanvas offcanvas-end" style={{ width: 460 }} tabIndex={-1} id="offcanvas_user_form">
        <div className="offcanvas-header border-bottom">
          <h5 className="mb-0">{editId ? "Edit User" : "Add New User"}</h5>
          <button type="button" className="btn-close" data-bs-dismiss="offcanvas" />
        </div>
        <div className="offcanvas-body">
          {formError && <div className="alert alert-danger py-2 fs-13">{formError}</div>}
          <div className="row g-3">
            {!editId && (
              <div className="col-12">
                <label className="form-label">Username <span className="text-danger">*</span></label>
                <input className="form-control" value={form.username}
                  onChange={e => setForm({ ...form, username: e.target.value })} />
              </div>
            )}
            <div className="col-md-6">
              <label className="form-label">First Name <span className="text-danger">*</span></label>
              <input className="form-control" value={form.firstname}
                onChange={e => setForm({ ...form, firstname: e.target.value })} />
            </div>
            <div className="col-md-6">
              <label className="form-label">Last Name <span className="text-danger">*</span></label>
              <input className="form-control" value={form.lastname}
                onChange={e => setForm({ ...form, lastname: e.target.value })} />
            </div>
            <div className="col-md-6">
              <label className="form-label">Email <span className="text-danger">*</span></label>
              <input type="email" className="form-control" value={form.email}
                onChange={e => setForm({ ...form, email: e.target.value })} />
            </div>
            <div className="col-md-6">
              <label className="form-label">Phone</label>
              <input className="form-control" value={form.phone}
                onChange={e => setForm({ ...form, phone: e.target.value })} />
            </div>
            <div className="col-md-6">
              <label className="form-label d-flex align-items-center gap-1">
                Role <span className="text-danger">*</span>
                <span
                  data-bs-toggle="tooltip"
                  data-bs-placement="top"
                  data-bs-title="The user's role controls what they can access. Administrator = full access, Supervisor = team lead, Counsellor = agent/first-line support."
                  style={{ cursor: 'help' }}>
                  <i className="ti ti-help-circle text-muted fs-14" />
                </span>
              </label>
              <select className="form-select" value={form.role}
                onChange={e => setForm({ ...form, role: e.target.value })}>
                <option value="">Select Role</option>
                {(formMeta.roles || []).map((r: any) => (
                  <option key={r.id} value={r.id} title={r.role_description}>{r.role_name}</option>
                ))}
              </select>
              {form.role && formMeta.roles.find((r: any) => String(r.id) === String(form.role))?.role_description && (
                <p className="text-muted fs-12 mt-1 mb-0">
                  <i className="ti ti-info-circle me-1" />
                  {formMeta.roles.find((r: any) => String(r.id) === String(form.role))?.role_description}
                </p>
              )}
            </div>
            <div className="col-md-6">
              <label className="form-label d-flex align-items-center gap-1">
                Extension
                <span
                  data-bs-toggle="tooltip"
                  data-bs-placement="top"
                  data-bs-title="A phone extension (SIP endpoint) assigns this user a direct line for receiving calls. Leave blank if the user doesn't handle calls."
                  style={{ cursor: 'help' }}>
                  <i className="ti ti-help-circle text-muted fs-14" />
                </span>
              </label>
              <select className="form-select" value={form.endpoint}
                onChange={e => setForm({ ...form, endpoint: e.target.value })}>
                <option value="">No Extension</option>
                {(formMeta.endpoints || []).map((ep: any) => (
                  <option key={ep.id} value={ep.id}>
                    {ep.id}{ep.context ? ` — ${ep.context}` : ''}{ep.ep_status ? ` (${ep.ep_status})` : ''}
                  </option>
                ))}
              </select>
              <p className="text-muted fs-12 mt-1 mb-0">
                <i className="ti ti-info-circle me-1" />Only unassigned extensions are shown.
              </p>
            </div>
            <div className="col-12">
              <label className="form-label">
                {editId ? "New Password" : "Password"}
                <span className="text-muted fs-12 ms-1">(leave blank to {editId ? "keep current" : "use username"})</span>
              </label>
              <input type="password" className="form-control" value={form.password}
                onChange={e => setForm({ ...form, password: e.target.value })} />
            </div>
          </div>
        </div>
        <div className="offcanvas-footer border-top p-3 d-flex gap-2 justify-content-end">
          <button type="button" className="btn btn-outline-secondary" data-bs-dismiss="offcanvas">Cancel</button>
          <button type="button" className="btn btn-primary" onClick={handleSave} disabled={saving}>
            {saving
              ? <><span className="spinner-border spinner-border-sm me-1" />Saving…</>
              : editId ? "Save Changes" : "Create User"}
          </button>
        </div>
      </div>

      {/* ── Delete Modal ───────────────────────────────────────────────────── */}
      <div className="modal fade" id="modal_delete_user" tabIndex={-1}>
        <div className="modal-dialog modal-dialog-centered">
          <div className="modal-content">
            <div className="modal-body text-center py-4">
              <i className="ti ti-trash-x fs-1 text-danger mb-3 d-block" />
              <h5>Delete User</h5>
              <p className="text-muted mb-0">
                Are you sure you want to delete{" "}
                <strong>{deleteTarget?.firstname} {deleteTarget?.lastname}</strong>?
                This cannot be undone.
              </p>
            </div>
            <div className="modal-footer justify-content-center gap-2 border-0 pt-0">
              <button type="button" className="btn btn-outline-secondary" data-bs-dismiss="modal">Cancel</button>
              <button type="button" className="btn btn-danger" onClick={handleDeleteConfirm}>Delete</button>
            </div>
          </div>
        </div>
      </div>
    </>
  );
}

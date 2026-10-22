import { useDispatch, useSelector } from "react-redux";
import { updateTheme } from "../../core/redux/themeSlice";
import { useEffect, useMemo, useState } from "react";
import { setExpandMenu, setMobileSidebar } from "../../core/redux/sidebarSlice";
import { Link, useLocation, useNavigate } from "react-router";
import { OverlayScrollbarsComponent } from "overlayscrollbars-react";
import "overlayscrollbars/overlayscrollbars.css";
import { SidebarData } from "./sidebarData";
import React from "react";
import { all_routes } from "../../routes/all_routes";
import soinLogo from "../../../public/soinLogo.jpeg";
import API from "../../services/api";

// Frontend action mapping directly to your DRF viewset custom action
export const getAuthenticatedUser = async () => {
  const response = await API.get(`users/me/`);
  return response.data;
};

const Sidebar = () => {
  const route = all_routes;
  const Location = useLocation();
  const pathname = Location.pathname;
  const [subsidebar, setSubsidebar] = useState("");
  const [openMenus, setOpenMenus] = useState<{ [label: string]: boolean }>({});
  const dispatch = useDispatch();

  // =========================================================================
  // LIVE PROFILE STATE MANAGEMENT (MATCHED TO NESTED JSON ROLE)
  // =========================================================================
  const [currentUser, setCurrentUser] = useState<any>(null);
  const [loadingUser, setLoadingUser] = useState(true);

  useEffect(() => {
    const fetchProfile = async () => {
      try {
        setLoadingUser(true);
        const data = await getAuthenticatedUser();
        setCurrentUser(data);
      } catch (error) {
        console.error("Failed to retrieve current user metadata context:", error);
        setCurrentUser(null);
      } finally {
        setLoadingUser(false);
      }
    };

    fetchProfile();
  }, []);

  
  // =========================================================================
  // ROLES
  // role name -> boolean flag the backend sets on the user (GET users/me/)
  // =========================================================================
  const ROLE_FLAGS = {
    farmer: "is_farmer",
    "vet officer": "is_vet_officer",
    agrovet: "is_agrovet",
    cooperative: "is_cooperative",
    slaughterhouse: "is_slaughterhouse",
    
  } as const;

  const resolveRole = (user: any): string => {
    if (!user) return "";
    // 1) boolean flags: is_farmer, is_vet_officer, ...
    const flagged = (Object.keys(ROLE_FLAGS) as (keyof typeof ROLE_FLAGS)[]).find(
      (role) => !!user[ROLE_FLAGS[role]]
    );
    if (flagged) return flagged;
    // 2) fall back to a role name: { role: { role_name } } or a plain string
    const named =
      user.role?.role_name ?? (typeof user.role === "string" ? user.role : "");
    return String(named).trim().toLowerCase();
  };

  const userRole = resolveRole(currentUser);
  const isSuperuser = !!currentUser?.is_superuser;

  // Only the menu items this role may see; sections left empty are dropped.
  const visibleMenu = useMemo(() => {
    const canSee = (item: any) =>
      isSuperuser ||
      !item?.roles ||
      item.roles.some((r: string) => r.trim().toLowerCase() === userRole);

    return (SidebarData as any[])
      .map((section) => ({
        ...section,
        submenuItems: section.submenuItems.filter(canSee),
      }))
      .filter((section) => section.submenuItems.length > 0);
  }, [userRole, isSuperuser]);

  // =========================================================================
  // SINGLE-ACTIVE-LINK RESOLUTION
  // -------------------------------------------------------------------------
  // Instead of letting every level of the menu (top item / sub item / sub-sub
  // item) independently decide "am I active?" - which lets a parent AND a
  // child AND an unrelated sibling all light up at once whenever their
  // relatedRoutes happen to overlap - we walk the whole tree once, collect
  // every node whose link/relatedRoutes match the current pathname, and then
  // pick exactly one "winner": the deepest (most specific) match. Only that
  // node, plus its direct ancestor chain (so the right submenus expand), are
  // considered active. Everything else is forced inactive.
  // =========================================================================
  type ActivePath = {
    topLabel?: string;
    midLabel?: string;
    leafLabel?: string;
  };

  const activePath: ActivePath = useMemo(() => {
    const matchesPath = (node: any, targetLink?: string) => {
      if (!node) return false;
      const link = targetLink ?? node?.link;
      if (link === pathname) return true;
      if (node?.relatedRoutes && node.relatedRoutes.includes(pathname)) return true;
      return false;
    };

    let best: { depth: number; topLabel?: string; midLabel?: string; leafLabel?: string } | null = null;

    visibleMenu.forEach((mainLabel: any) => {
      mainLabel?.submenuItems?.forEach((title: any) => {
        const targetLink = title?.label === "Dashboard" ? route.dashboard : title?.link;

        // depth 1: the top-level menu item itself
        if (matchesPath(title, targetLink)) {
          if (!best || best.depth < 1) {
            best = { depth: 1, topLabel: title?.label };
          }
        }

        title?.submenuItems?.forEach((item: any) => {
          // depth 2: a direct child
          if (matchesPath(item)) {
            if (!best || best.depth < 2) {
              best = { depth: 2, topLabel: title?.label, midLabel: item?.label };
            }
          }

          item?.submenuItems?.forEach((subitem: any) => {
            // depth 3: a grandchild (the deepest, most specific match)
            if (matchesPath(subitem)) {
              if (!best || best.depth < 3) {
                best = {
                  depth: 3,
                  topLabel: title?.label,
                  midLabel: item?.label,
                  leafLabel: subitem?.label,
                };
              }
            }
          });
        });
      });
    });

    return best ?? {};
  }, [pathname, route.dashboard, visibleMenu]);

  // On mount or pathname change, auto-open only the submenu that contains
  // the single active node resolved above (instead of opening every menu
  // whose contents happened to match independently).
  useEffect(() => {
    if (loadingUser) return;

    setOpenMenus((prev) => {
      const next = { ...prev };
      if (activePath.topLabel) {
        next[activePath.topLabel] = true;
      }
      return next;
    });

    if (activePath.midLabel) {
      setSubsidebar(activePath.midLabel);
    }
  }, [pathname, loadingUser, activePath]);

  const handleMenuToggle = (label: string) => {
    setOpenMenus((prev) => ({ ...prev, [label]: !prev[label] }));
  };

  const toggleSubsidebar = (subitem: any) => {
    if (subitem === subsidebar) {
      setSubsidebar("");
    } else {
      setSubsidebar(subitem);
    }
  };

  const handleClick = (label: any) => {
    handleMenuToggle(label);
  };

  const navigate = useNavigate();
  const themeSettings = useSelector((state: any) => state.theme.themeSettings);

  const handleMiniSidebar = () => {
    const rootElement = document.documentElement;
    const isMini = rootElement.getAttribute("data-layout") === "mini";
    const updatedLayout = isMini ? "default" : "mini";
    dispatch(
      updateTheme({
        "data-layout": updatedLayout,
      })
    );
    if (isMini) {
      rootElement.classList.remove("mini-sidebar");
    } else {
      rootElement.classList.add("mini-sidebar");
    }
  };
  const onMouseEnter = () => { dispatch(setExpandMenu(true)); };
  const onMouseLeave = () => { dispatch(setExpandMenu(false)); };

  const handleLayoutClick = (layout: string) => {
    const layoutSettings: any = { "data-layout": "default", dir: "ltr" };
    switch (layout) {
      case "Default": layoutSettings["data-layout"] = "default"; break;
      case "Hidden": layoutSettings["data-layout"] = "hidden"; break;
      case "Mini": layoutSettings["data-layout"] = "mini"; break;
      case "Hover View": layoutSettings["data-layout"] = "hoverview"; break;
      case "Full Width": layoutSettings["data-layout"] = "full-width"; break;
      case "Dark": layoutSettings["data-bs-theme"] = "dark"; break;
      case "RTL": layoutSettings.dir = "rtl"; break;
      default: break;
    }
    dispatch(updateTheme(layoutSettings));
    navigate("/dashboard");
  };

  const mobileSidebar = useSelector((state: any) => state.sidebarSlice.mobileSidebar);
  const toggleMobileSidebar = () => { dispatch(setMobileSidebar(!mobileSidebar)); };

  useEffect(() => {
    const rootElement: any = document.documentElement;
    Object.entries(themeSettings).forEach(([key, value]) => {
      rootElement.setAttribute(key, value);
    });
    if (themeSettings["data-layout"] === "mini") {
      rootElement.classList.add("mini-sidebar");
    } else {
      rootElement.classList.remove("mini-sidebar");
    }
  }, [themeSettings]);

  // Prevent UI frame popping/collapsing during layout authorization lookup
  if (loadingUser) {
    return <div className="sidebar" id="sidebar" style={{ width: "260px" }} />;
  }

  // =========================================================================
  // CONDITIONAL RENDER BREAKOUT
  // =========================================================================
  if (visibleMenu.length === 0) {
    return null;
  }

  return (
    <>
      <div
        className="sidebar"
        id="sidebar"
        onMouseEnter={onMouseEnter}
        onMouseLeave={onMouseLeave}
      >
        <div className="sidebar-logo">
          <div style={{  display: "flex", alignItems: "center", overflow: "hidden", position: "relative" }}>
            <Link to={route.dashboard} className="logo logo-normal" style={{ lineHeight: 0 }}>
              <img src={soinLogo} alt="Childline Kenya" style={{ height: 36, maxWidth: 150, objectFit: "contain" }} />
            </Link>
            <Link to={route.dashboard} className="logo-small" style={{ lineHeight: 0 }}>
              <img src={soinLogo} alt="CLK" style={{ height: 30, width: 30, objectFit: "contain" }} />
            </Link>
            <Link to={route.dashboard} className="dark-logo" style={{ lineHeight: 0 }}>
              <img src={soinLogo} alt="Childline Kenya" style={{ height: 36, maxWidth: 150, objectFit: "contain", filter: "brightness(0) invert(1)" }} />
            </Link>
          </div>
          <button className="sidenav-toggle-btn btn border-0 p-0 active" id="toggle_btn" onClick={handleMiniSidebar}>
            <i className="ti ti-arrow-bar-to-left" />
          </button>
          <button className="sidebar-close" onClick={toggleMobileSidebar}>
            <i className="ti ti-x align-middle" />
          </button>
        </div>

        <div className="sidebar-inner" data-simplebar="">
          <OverlayScrollbarsComponent style={{ height: "100%", width: "100%",top:"50px" }}>
            <div id="sidebar-menu" className="sidebar-menu">
              <ul>
                {visibleMenu.map((mainLabel: any, index: number) => (
                  <React.Fragment key={`main-${index}`}>
                    <li className="menu-title">
                      <span>{mainLabel?.tittle}</span>
                    </li>
                    <li>
                      <ul>
                        {mainLabel?.submenuItems?.map((title: any, i: number) => {
                          // -------------------------------------------------------------
                          // DYNAMIC ROUTE FIX FOR THE DASHBOARD ITEM
                          // -------------------------------------------------------------
                          const targetLink = title?.label === "Dashboard" ? route.dashboard : title?.link;

                          // Only ever the single resolved top-level winner is active.
                          const isActive = activePath.topLabel === title?.label && !activePath.midLabel;
                          const isMenuOpen = openMenus[title?.label] || false;

                          return (
                            <li className="submenu" key={`title-${i}`}>
                              <Link
                                to={title?.submenu ? "#" : targetLink}
                                onClick={() => {
                                  handleClick(title?.label);
                                  if (mainLabel?.tittle === "Layout") { handleLayoutClick(title?.label); }
                                }}
                                className={`${isActive ? "active" : ""} ${isActive && isMenuOpen && title?.submenu ? "subdrop" : ""}`}
                              >
                                <i className={`ti ti-${title.icon}`}></i>
                                <span>{title?.label}</span>
                                {(title?.submenu || title?.customSubmenuTwo) && ( <span className="menu-arrow"></span> )}
                              </Link>

                              {title?.submenu !== false && (
                                <ul style={{ display: isMenuOpen ? "block" : "none" }}>
                                  {title?.submenuItems?.map((item: any, j: any) => {
                                      // Only the resolved mid-level winner is active, and only
                                      // when it belongs to this top-level menu, and only when
                                      // there's no deeper (leaf) winner underneath it.
                                      const isSubActive =
                                        activePath.topLabel === title?.label &&
                                        activePath.midLabel === item?.label &&
                                        !activePath.leafLabel;
                                      return (
                                        <li className={`${item?.submenuItems ? "submenu submenu-two" : ""} `} key={`item-${j}`}>
                                          <Link
                                            to={item?.submenu ? "#" : item?.link}
                                            className={`${isSubActive ? "active subdrop" : ""}`}
                                            onClick={() => {
                                              toggleSubsidebar(item?.label);
                                              if (title?.label === "Layouts") { handleLayoutClick(item?.label); }
                                            }}
                                          >
                                            {item?.label}
                                            {(item?.submenu || item?.customSubmenuTwo) && ( <span className="menu-arrow"></span> )}
                                          </Link>
                                          {item?.submenuItems ? (
                                            <ul style={{ display: subsidebar === item?.label ? "block" : "none" }}>
                                              {item?.submenuItems?.map((items: any, k: any) => {
                                                  // Only the resolved leaf winner is active, and
                                                  // only when it belongs to this exact branch.
                                                  const isSubSubActive =
                                                    activePath.topLabel === title?.label &&
                                                    activePath.midLabel === item?.label &&
                                                    activePath.leafLabel === items?.label;
                                                  return (
                                                    <li key={`submenu-item-${k}`}>
                                                      <Link to={items?.submenu ? "#" : items?.link} className={`${isSubSubActive ? "active" : ""}`}>
                                                        {items?.label}
                                                      </Link>
                                                    </li>
                                                  );
                                                }
                                              )}
                                            </ul>
                                          ) : null}
                                        </li>
                                      );
                                    }
                                  )}
                                </ul>
                              )}
                            </li>
                          );
                        })}
                      </ul>
                    </li>
                  </React.Fragment>
                ))}
              </ul>
            </div>
          </OverlayScrollbarsComponent>
        </div>
      </div>
    </>
  );
};

export default Sidebar;

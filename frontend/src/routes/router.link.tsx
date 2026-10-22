import { Route } from "react-router";
import { all_routes } from "./all_routes";

import Login from "../pages/auth/login/login";
import Register from "../pages/auth/register/register";

import SourcesDashboard from "../pages/users/manager/dashboards/sources";
import ProductsList from "../pages/products/ProductsList";
import ProductDetail from "../pages/products/ProductDetail";
import PaymentsList from "../pages/payments/PaymentsList";
import CpdPage from "../pages/cpd/CpdPage";
import ExamPage from "../pages/cpd/ExamPage";
import ZoomPage from "../pages/zoom/ZoomPage";

import SalesList from "../pages/sales/SalesList";
import CustomersList from "../pages/customers/CustomersList";
import StockMovementsList from "../pages/stock/StockMovementsList";


import Users from "../pages/users/manager/dashboards/users";
import AdminDashboard from "../pages/users/admin/dashboard/dashboard";
import SystemLogs from "../pages/admin/SystemLogs";
import DynamicDashboardWrapper from "./dynamicRoute";

const route = all_routes;

// ─── Role names ──────────────────────────────────────────────────────────────
// These must match the role_name values in your Roles table. Create them with:
//   Administrator, Official, Farmer, Vet Officer, Agrovet, Cooperative,
//   Slaughterhouse
// ProtectedRoute should compare them case-insensitively.
export const ROLES = {
  ADMIN: "Administrator",
  OFFICIAL: "Official",
  FARMER: "Farmer",
  VET: "Vet Officer",
  AGROVET: "Agrovet",
  COOPERATIVE: "Cooperative",
  SLAUGHTERHOUSE: "Slaughterhouse",
};

const ALL_ROLES = Object.values(ROLES);

// Agrovet staff run the shop: POS, stock, sales, customers, payments
const SHOP_ROLES = [ROLES.ADMIN, ROLES.AGROVET];

// Roles that can browse the product catalogue
const CATALOGUE_ROLES = [
  ROLES.ADMIN,
  ROLES.AGROVET,
  ROLES.VET,
  ROLES.FARMER,
];

export const publicRoutes = [
  // ── Everyone (logged in) ────────────────────────────────────────────────
  {
    id: "200",
    path: route.portal,
    element: <DynamicDashboardWrapper />,
    route: Route,
    meta_title: "Dashboard",
    roles: ALL_ROLES,
  },

  // ── Catalogue ───────────────────────────────────────────────────────────
  {
    id: "203",
    path: route.products,
    element: <ProductsList />,
    route: Route,
    meta_title: "Products",
    roles: CATALOGUE_ROLES,
  },
  {
    id: "204",
    path: `${route.productDetail}/:id`,
    element: <ProductDetail />,
    route: Route,
    meta_title: "Product Detail",
    roles: CATALOGUE_ROLES,
  },


  {
    id: "198",
    path: route.cpd,
    element: <CpdPage />,
    route: Route,
    meta_title: "Cpd",
    roles: CATALOGUE_ROLES,
  },
  {
    id: "198",
    path: `${route.exam}/:tutorialId`,
    element: <ExamPage />,
    route: Route,
    meta_title: "Exam",
    roles: CATALOGUE_ROLES,
  },
  {
    id: "200",
    path: route.zoom,
    element: <ZoomPage />,
    route: Route,
    meta_title: "Zoom",
    roles: SHOP_ROLES,
  },
  {
    id: "155",
    path: route.sales,
    element: <SalesList />,
    route: Route,
    meta_title: "Sales",
    roles: SHOP_ROLES,
  },
  {
    id: "156",
    path: route.customers,
    element: <CustomersList />,
    route: Route,
    meta_title: "Customers",
    roles: SHOP_ROLES,
  },
  {
    id: "157",
    path: route.stock,
    element: <StockMovementsList />,
    route: Route,
    meta_title: "Stock Movements",
    roles: SHOP_ROLES,
  },
  {
    id: "159",
    path: route.payments,
    element: <PaymentsList />,
    route: Route,
    meta_title: "Payments",
    roles: SHOP_ROLES,
  },
  {
    id: "202",
    path: route.sourcesDashboard,
    element: <SourcesDashboard />,
    route: Route,
    meta_title: "Sources Dashboard",
    roles: SHOP_ROLES,
  },

  // ── Administrator only ──────────────────────────────────────────────────
  {
    id: "197",
    path: route.users,
    element: <Users />,
    route: Route,
    meta_title: "Users",
    roles: [ROLES.ADMIN],
  },
  {
    id: "208",
    path: route.systemLogs,
    element: <SystemLogs />,
    route: Route,
    meta_title: "System Logs",
    roles: [ROLES.ADMIN],
  },
  {
    id: "211",
    path: route.adminDashboard,
    element: <AdminDashboard />,
    route: Route,
    meta_title: "Admin Dashboard",
    roles: [ROLES.ADMIN],
  },
];

export const authRoutes = [
  {
    id: "auth-1",
    path: route.login,
    element: <Login />,
    route: Route,
    meta_title: "Login",
  },
  {
    id: "auth-2",
    path: route.register,
    element: <Register />,
    route: Route,
    meta_title: "Register",
  },
];

// Centralized routing so we can plug in Candidates/CandidateDetail later.
// ---------------------------------------------------------------------------
// import React from "react";
// import { createBrowserRouter, RouterProvider } from "react-router-dom";
// import Upload from "./pages/Upload";


// const router = createBrowserRouter([
// { path: "/", element: <Upload /> },
// { path: "/upload", element: <Upload /> },
// // Placeholders — you'll fill these in Phase 1.2/1.3
// { path: "/candidates", element: <div className="p-6">Candidates list (coming soon)</div> },
// { path: "/candidates/:id", element: <div className="p-6">Candidate detail (coming soon)</div> },
// ]);


// export default function AppRoutes() {
// return <RouterProvider router={router} />;
// }

import React from "react";
import { createBrowserRouter, RouterProvider } from "react-router-dom";
import Upload from "./pages/Upload";
import Candidates from "./pages/Candidates";
import CandidateDetail from "./pages/CandidateDetail";

const router = createBrowserRouter([
  { path: "/", element: <Upload /> },
  { path: "/upload", element: <Upload /> },
  { path: "/candidates", element: <Candidates /> },
  { path: "/candidates/:id", element: <CandidateDetail /> },
]);

export default function AppRoutes() {
  return <RouterProvider router={router} />;
}

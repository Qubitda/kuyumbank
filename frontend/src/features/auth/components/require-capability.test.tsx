import { describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { RequireCapability } from "./require-capability";

vi.mock("./auth-provider", () => ({
  useAuthContext: vi.fn(),
}));

import { useAuthContext } from "./auth-provider";

const mockedUseAuth = vi.mocked(useAuthContext);

function wrap(ui: React.ReactNode) {
  return render(<MemoryRouter>{ui}</MemoryRouter>);
}

describe("RequireCapability", () => {
  it("yetkisiz kullanıcıya 403 gösterir", () => {
    mockedUseAuth.mockReturnValue({
      user: {
        id: 1,
        username: "buyer",
        rol: "ALICI",
        firma: null,
        firma_id: 1,
        capabilities: {
          can_view_catalog: true,
        },
        email_verified: true,
        act_as: { active: false },
      },
      loading: false,
      error: null,
      mfaPending: false,
      isAuthenticated: true,
      refresh: vi.fn(),
      setSessionUser: vi.fn(),
      logout: vi.fn(),
    } as never);

    wrap(
      <RequireCapability capability="can_manage_org">
        <div>Gizli içerik</div>
      </RequireCapability>
    );

    expect(screen.getByRole("alert")).toHaveTextContent(/yetkiniz yok/i);
    expect(screen.queryByText("Gizli içerik")).toBeNull();
  });

  it("yetkili kullanıcıya içeriği gösterir", () => {
    mockedUseAuth.mockReturnValue({
      user: {
        id: 1,
        username: "ops",
        rol: "PLATFORM",
        firma: null,
        firma_id: 1,
        capabilities: { can_manage_org: true },
        email_verified: true,
        act_as: { active: false },
      },
      loading: false,
      error: null,
      mfaPending: false,
      isAuthenticated: true,
      refresh: vi.fn(),
      setSessionUser: vi.fn(),
      logout: vi.fn(),
    } as never);

    wrap(
      <RequireCapability capability="can_manage_org">
        <div>Gizli içerik</div>
      </RequireCapability>
    );

    expect(screen.getByText("Gizli içerik")).toBeInTheDocument();
  });
});

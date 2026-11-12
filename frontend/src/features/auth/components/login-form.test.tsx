import { describe, expect, it, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { LoginForm } from "./login-form";

const login = vi.fn();
const verifyMfa = vi.fn();
const resendMfa = vi.fn();
const setSessionUser = vi.fn();

vi.mock("../services/auth-service", () => ({
  authService: {
    login: (...args: unknown[]) => login(...args),
    verifyMfa: (...args: unknown[]) => verifyMfa(...args),
    resendMfa: (...args: unknown[]) => resendMfa(...args),
  },
}));

vi.mock("../hooks/use-auth", () => ({
  useAuth: () => ({
    setSessionUser,
    refresh: vi.fn(),
    mfaPending: false,
  }),
}));

describe("LoginForm", () => {
  beforeEach(() => {
    login.mockReset();
    verifyMfa.mockReset();
    resendMfa.mockReset();
    setSessionUser.mockReset();
  });

  it("başarılı login sonrası setSessionUser çağırır", async () => {
    const user = userEvent.setup();
    login.mockResolvedValue({
      id: 1,
      username: "demo",
      rol: "ALICI",
      firma: null,
      firma_id: 1,
      capabilities: {},
      email_verified: true,
      act_as: { active: false },
    });

    render(
      <MemoryRouter>
        <LoginForm />
      </MemoryRouter>
    );

    await user.type(screen.getByLabelText(/kullanıcı adı/i), "demo");
    await user.type(screen.getByLabelText(/^parola$/i), "secret123");
    await user.click(screen.getByRole("button", { name: /giriş yap/i }));

    await waitFor(() => expect(login).toHaveBeenCalled());
    expect(setSessionUser).toHaveBeenCalled();
  });

  it("MFA gerekliyse kod alanını gösterir", async () => {
    const user = userEvent.setup();
    login.mockResolvedValue({
      id: 1,
      username: "demo",
      rol: "ALICI",
      firma: null,
      firma_id: 1,
      capabilities: {},
      email_verified: true,
      act_as: { active: false },
      mfa_required: true,
      mfa_ok: false,
    });

    render(
      <MemoryRouter>
        <LoginForm />
      </MemoryRouter>
    );

    await user.type(screen.getByLabelText(/kullanıcı adı/i), "demo");
    await user.type(screen.getByLabelText(/^parola$/i), "secret123");
    await user.click(screen.getByRole("button", { name: /giriş yap/i }));

    await waitFor(() =>
      expect(screen.getByLabelText(/doğrulama kodu/i)).toBeInTheDocument()
    );
  });
});

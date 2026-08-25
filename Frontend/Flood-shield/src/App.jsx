import { useMemo, useState, useEffect } from "react";
import "./App.css";
import {
  loginUser, registerUser, createBusiness, getBusinesses,
  getInventory, addInventoryItem, getRisk,
  getWarehouseRec, getVehicleMatch,
  mapApiItem, mapFormToApi,
} from "./api";

const nav = [
  ["Dashboard", "grid"],
  ["Inventory", "box"],
  ["Risk intelligence", "activity"],
  ["Safe routes", "route"],
  ["Storage", "warehouse"],
  ["Transport", "truck"],
  ["Action plan", "clipboard"],
];
const starterItems = [
  {
    id: 1,
    name: "Rice & dry supplies",
    category: "Essential food",
    quantity: 240,
    value: 156000,
    location: "Riverside Depot",
    priority: 95,
    risk: "High",
  },
  {
    id: 2,
    name: "Portable water filters",
    category: "Relief equipment",
    quantity: 85,
    value: 102000,
    location: "Riverside Depot",
    priority: 88,
    risk: "High",
  },
  {
    id: 3,
    name: "First-aid kits",
    category: "Medical supplies",
    quantity: 140,
    value: 84000,
    location: "Central Store",
    priority: 76,
    risk: "Medium",
  },
  {
    id: 4,
    name: "Blankets",
    category: "Relief equipment",
    quantity: 310,
    value: 93000,
    location: "Central Store",
    priority: 61,
    risk: "Low",
  },
];
const planTasks = [
  {
    id: 1,
    time: "NOW · NEXT 2 HOURS",
    title: "Move water filters to North Hub",
    detail: "Use the approved safe route via Ring Road.",
  },
  {
    id: 2,
    time: "TODAY",
    title: "Dispatch dry supplies to Sector 4",
    detail: "Demand at the East Relief Camp has increased.",
  },
  {
    id: 3,
    time: "BEFORE 18:00",
    title: "Seal Riverside Depot stock",
    detail: "Raise palletized supplies above the expected waterline.",
  },
];
const initialNotifications = [
  {
    id: 1,
    color: "red",
    title: "Flood warning: Riverside Depot",
    text: "Water level is rising. Review priority stock now.",
    read: false,
  },
  {
    id: 2,
    color: "amber",
    title: "Rainfall update",
    text: "Heavy rain is expected from 18:00 today.",
    read: false,
  },
  {
    id: 3,
    color: "green",
    title: "Safe route refreshed",
    text: "North Ring Road remains clear for transport.",
    read: false,
  },
  {
    id: 4,
    color: "blue",
    title: "Inventory assessment complete",
    text: "Two high-priority stock items need attention.",
    read: true,
  },
  {
    id: 5,
    color: "green",
    title: "Response plan is ready",
    text: "Three recommended actions are available to review.",
    read: true,
  },
];

function Icon({ name, size = 20 }) {
  const paths = {
    grid: (
      <>
        <rect x="3" y="3" width="7" height="7" rx="1" />
        <rect x="14" y="3" width="7" height="7" rx="1" />
        <rect x="3" y="14" width="7" height="7" rx="1" />
        <rect x="14" y="14" width="7" height="7" rx="1" />
      </>
    ),
    box: (
      <>
        <path d="m3 8 9-5 9 5v9l-9 5-9-5Z" />
        <path d="m3 8 9 5 9-5M12 13v9" />
      </>
    ),
    activity: <path d="M3 12h4l2.3-7 4.4 14 2.3-7H21" />,
    route: (
      <>
        <circle cx="6" cy="18" r="2.5" />
        <circle cx="18" cy="6" r="2.5" />
        <path d="M8.2 16.7c5.2-1.2 1.4-7 7.7-8.7" />
      </>
    ),
    warehouse: (
      <>
        <path d="m3 10 9-6 9 6v10H3Z" />
        <path d="M3 10h18M8 14h2v6H8zm6 0h2v6h-2z" />
      </>
    ),
    truck: (
      <>
        <path d="M3 6h11v11H3zM14 10h4l3 3v4h-7Z" />
        <circle cx="7" cy="19" r="2" />
        <circle cx="18" cy="19" r="2" />
      </>
    ),
    clipboard: (
      <>
        <rect x="5" y="4" width="14" height="17" rx="2" />
        <path d="M9 4.5V3h6v1.5M8.5 10h7M8.5 14h7M8.5 18h4" />
      </>
    ),
    bell: (
      <>
        <path d="M18 9a6 6 0 0 0-12 0c0 7-3 7-3 9h18c0-2-3-2-3-9M10 21h4" />
      </>
    ),
    menu: <path d="M4 7h16M4 12h16M4 17h16" />,
    close: <path d="m6 6 12 12M18 6 6 18" />,
    plus: <path d="M12 5v14M5 12h14" />,
    arrow: <path d="M5 12h14M13 6l6 6-6 6" />,
    search: (
      <>
        <circle cx="11" cy="11" r="6.5" />
        <path d="m16 16 4 4" />
      </>
    ),
    pin: (
      <>
        <path d="M20 10c0 5-8 11-8 11S4 15 4 10a8 8 0 1 1 16 0Z" />
        <circle cx="12" cy="10" r="2.5" />
      </>
    ),
    shield: (
      <>
        <path d="M12 3 20 6v5c0 5-3.4 8.4-8 10-4.6-1.6-8-5-8-10V6Z" />
        <path d="m8.5 12 2.2 2.2 4.8-5" />
      </>
    ),
    clock: (
      <>
        <circle cx="12" cy="12" r="8.5" />
        <path d="M12 7v5l3.5 2" />
      </>
    ),
    trash: (
      <>
        <path d="M4 7h16M10 11v6M14 11v6M9 7l1-3h4l1 3M6 7l1 14h10l1-14" />
      </>
    ),
    check: <path d="m5 12 4.2 4.2L19 6.5" />,
    download: (
      <>
        <path d="M12 3v12M7 10l5 5 5-5M5 21h14" />
      </>
    ),
    external: (
      <>
        <path d="M14 4h6v6M20 4l-9 9M18 13v5a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h5" />
      </>
    ),
    chevron: <path d="m9 18 6-6-6-6" />,
    user: (
      <>
        <circle cx="12" cy="8" r="3.5" />
        <path d="M5 21c.5-4 3-6 7-6s6.5 2 7 6" />
      </>
    ),
    camera: (
      <>
        <path d="M4 8h3l1.5-2h7L17 8h3a2 2 0 0 1 2 2v8a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2v-8a2 2 0 0 1 2-2Z" />
        <circle cx="12" cy="14" r="3.5" />
      </>
    ),
    edit: (
      <>
        <path d="m13.5 6.5 4 4M4 20l3.6-.8L19 7.8a2.8 2.8 0 0 0-4-4L3.6 15.2 3 19.8Z" />
      </>
    ),
    logout: (
      <>
        <path d="M10 5H5a2 2 0 0 0-2 2v10a2 2 0 0 0 2 2h5" />
        <path d="M14 8l4 4-4 4M18 12H8" />
      </>
    ),
    warning: (
      <>
        <path d="M12 3 2.8 20h18.4Z" />
        <path d="M12 9v4.5M12 17h.01" />
      </>
    ),
    cloud: (
      <>
        <path d="M7 18h10a4 4 0 0 0 .4-8A6 6 0 0 0 6.4 8.1 5 5 0 0 0 7 18Z" />
        <path d="M8 21c.5-.6.8-1.2.8-2M12 21c.5-.6.8-1.2.8-2M16 21c.5-.6.8-1.2.8-2" />
      </>
    ),
    location: (
      <>
        <path d="M12 21s7-6.3 7-12a7 7 0 1 0-14 0c0 5.7 7 12 7 12Z" />
        <circle cx="12" cy="9" r="2.2" />
      </>
    ),
  };
  return (
    <svg
      className="icon"
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.8"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
    >
      {paths[name] || paths.grid}
    </svg>
  );
}

function App() {
  const [page, setPage] = useState("Dashboard");
  const [pageHistory, setPageHistory] = useState([]);
  const [menu, setMenu] = useState(false);
  const [alerts, setAlerts] = useState(false);
  const [notifications, setNotifications] = useState(initialNotifications);
  const [modal, setModal] = useState(null);
  const [notice, setNotice] = useState("");
  const [items, setItems] = useState(starterItems);
  const [search, setSearch] = useState("");
  const [route, setRoute] = useState("North Ring Road");
  const [done, setDone] = useState([]);
  const [form, setForm] = useState({
    name: "",
    category: "Essential food",
    quantity: "",
    value: "",
    location: "Riverside Depot",
  });
  const [signedIn, setSignedIn] = useState(false);
  const [token, setToken] = useState(null);
  const [businessId, setBusinessId] = useState(null);
  const [riskData, setRiskData] = useState(null);
  const [warehouseRec, setWarehouseRec] = useState(null);
  const [vehicleMatch, setVehicleMatch] = useState(null);
  const [loginForm, setLoginForm] = useState({
    email: "aaryan.mehta@example.com",
    password: "",
  });
  const [profileData, setProfileData] = useState({
    name: "Aaryan Mehta",
    role: "Business owner",
    email: "aaryan.mehta@example.com",
    phone: "+91 98765 43210",
    organisation: "Mehta Relief Operations",
    location: "Riverside, India",
    photo: "",
  });
  const highItems = items.filter((item) => item.risk === "High");
  const totalValue = items.reduce((total, item) => total + item.value, 0);
  const filtered = useMemo(
    () =>
      items.filter(
        (item) =>
          item.name.toLowerCase().includes(search.toLowerCase()) ||
          item.location.toLowerCase().includes(search.toLowerCase()),
      ),
    [items, search],
  );
  const flash = (text) => {
    setNotice(text);
    window.setTimeout(() => setNotice(""), 3200);
  };
  const navigate = (next) => {
    if (next !== page) {
      setPageHistory((history) => [...history.slice(-9), page]);
      setPage(next);
    }
    setAlerts(false);
  };
  const goBack = () => {
    const previousPage = pageHistory.at(-1);
    if (!previousPage) return;
    setPageHistory((history) => history.slice(0, -1));
    setPage(previousPage);
    setAlerts(false);
  };
  const unreadNotifications = notifications.filter((item) => !item.read).length;
  const toggleNotifications = () => setAlerts((open) => !open);
  const markAllNotificationsRead = () =>
    setNotifications((current) =>
      current.map((notification) => ({ ...notification, read: true })),
    );
  const markNotificationRead = (id) =>
    setNotifications((current) =>
      current.map((notification) =>
        notification.id === id ? { ...notification, read: true } : notification,
      ),
    );
  const openAccount = () => {
    setMenu(false);
    navigate(signedIn ? "Profile" : "Login");
  };
  const signIn = async (event) => {
    event.preventDefault();
    if (!loginForm.email.includes("@") || loginForm.password.length < 6) {
      flash("Enter a valid email and a password with at least 6 characters.");
      return;
    }
    try {
      flash("Connecting to FloodShield backend...");
      let data;
      try {
        data = await loginUser(loginForm.email, loginForm.password);
      } catch {
        // Auto-register if not found
        await registerUser(loginForm.email, loginForm.password,
          loginForm.email.split("@")[0]);
        data = await loginUser(loginForm.email, loginForm.password);
      }
      const jwt = data.access_token;
      setToken(jwt);

      // Get or create business
      let bizId = null;
      try {
        const businesses = await getBusinesses(jwt);
        if (businesses && businesses.length > 0) {
          bizId = businesses[0].id;
        } else {
          const biz = await createBusiness({
            name: profileData.organisation || "My Business",
            address: profileData.location || "India",
            city: "Mumbai", state: "Maharashtra",
            pincode: "400001",
            latitude: 19.076, longitude: 72.877,
            business_type: "retail", employee_count: 5,
          }, jwt);
          bizId = biz.id;
        }
      } catch { bizId = 1; }

      setBusinessId(bizId);

      // Load inventory from backend
      try {
        const inv = await getInventory(bizId, jwt);
        if (inv && inv.length > 0) setItems(inv.map(mapApiItem));
      } catch { /* keep mock data */ }

      // Load risk, warehouse, vehicle in background
      getRisk(bizId, jwt).then(setRiskData).catch(() => {});
      getWarehouseRec(bizId, jwt).then(setWarehouseRec).catch(() => {});
      getVehicleMatch(bizId, jwt).then(setVehicleMatch).catch(() => {});

      setProfileData((c) => ({ ...c, email: loginForm.email }));
      setSignedIn(true);
      setMenu(false);
      navigate("Profile");
      flash("Signed in! Live data loaded from FloodShield backend.");
    } catch (err) {
      flash(err.message || "Login failed. Please try again.");
    }
  };
  const signOut = () => {
    setSignedIn(false);
    setLoginForm((current) => ({ ...current, password: "" }));
    setMenu(false);
    navigate("Login");
    flash("You have been signed out.");
  };
  const addItem = () => {
    setForm({
      name: "",
      category: "Essential food",
      quantity: "",
      value: "",
      location: "Riverside Depot",
    });
    setModal("inventory");
  };
  const saveItem = async (event) => {
    event.preventDefault();
    const quantity = Number(form.quantity);
    const value = Number(form.value);
    if (!form.name.trim() || quantity < 1 || value < 1) {
      flash("Please add an item name, quantity, and value.");
      return;
    }
    const priority = Math.min(
      98,
      Math.round(54 + Math.min(value / 5000, 34) + Math.min(quantity / 30, 12)),
    );
    const newItem = {
      id: Date.now(),
      ...form,
      quantity,
      value,
      priority,
      risk: form.location === "Riverside Depot" ? "High" : "Medium",
    };
    setItems((current) => [...current, newItem]);
    setModal(null);
    flash("Inventory added and included in risk analysis.");

    // Save to backend if logged in
    if (token && businessId) {
      try {
        await addInventoryItem(businessId, mapFormToApi(form), token);
      } catch { /* silently fail — local state already updated */ }
    }
  };
  const removeItem = (id) => {
    setItems((current) => current.filter((item) => item.id !== id));
    flash("Inventory item removed.");
  };
  const exportPlan = () => {
    const content = `FLOODSHIELD | Emergency Action Plan\n\nFlood risk: HIGH\nPriority stock: ${highItems.length} critical items\nSelected route: ${route}\n\n1. Move water filters to North Hub\n2. Dispatch dry supplies to Sector 4\n3. Seal Riverside Depot stock before 18:00`;
    const url = URL.createObjectURL(
      new Blob([content], { type: "text/plain" }),
    );
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = "floodshield-action-plan.txt";
    anchor.click();
    URL.revokeObjectURL(url);
    flash("Action plan downloaded.");
  };
  const isAuthenticationPage = page === "Login" || page === "Signup";
  const mainProps = {
    navigate,
    flash,
    setModal,
    highItems,
    totalValue,
    addItem,
    items,
    filtered,
    search,
    setSearch,
    removeItem,
    route,
    setRoute,
    done,
    setDone,
    exportPlan,
    profileData,
    riskData,
    warehouseRec,
    vehicleMatch,
  };
  return (
    <div className="app-shell">
      <aside className={`sidebar ${menu ? "is-open" : ""}`}>
        <div className="brand-wrap">
          <button className="brand" onClick={() => navigate("Dashboard")}>
            <span className="brand-mark">
              <i></i>
              <i></i>
              <i></i>
            </span>
            Flood<span>Shield</span>
          </button>
          {!isAuthenticationPage && (
            <button
              className="mobile-close"
              onClick={() => setMenu(false)}
              aria-label="Close menu"
            >
              <Icon name="close" />
            </button>
          )}
        </div>
        <p className="workspace-label">WORKSPACE</p>
        <nav>
          {nav.map(([label, icon]) => (
            <button
              key={label}
              className={`nav-link ${page === label ? "active" : ""}`}
              onClick={() => navigate(label)}
            >
              <Icon name={icon} size={19} />
              <span>{label}</span>
              {label === "Action plan" && <em>3</em>}
            </button>
          ))}
        </nav>
        <div className="sidebar-bottom">
          <div className="weather-card">
            <Icon name="cloud" size={25} />
            <div>
              <b>Heavy rainfall</b>
              <span>Expected in 5 hours</span>
            </div>
          </div>
          <button className="help-link" onClick={() => setModal("help")}>
            <i>?</i>Emergency help center <Icon name="external" size={14} />
          </button>
        </div>
      </aside>
      {menu && (
        <button
          className="overlay"
          onClick={() => setMenu(false)}
          aria-label="Close navigation"
        />
      )}
      <main className="main-content">
        <header className="topbar">
          {!isAuthenticationPage && (
            <>
              <button
                className="mobile-menu"
                onClick={() => setMenu((open) => !open)}
                aria-label={
                  menu ? "Close navigation menu" : "Open navigation menu"
                }
                aria-expanded={menu}
              >
                <Icon name={menu ? "close" : "menu"} />
              </button>
              <button
                className="icon-button back-button"
                onClick={goBack}
                disabled={pageHistory.length === 0}
                aria-label="Go back to the previous page"
              >
                <Icon name="arrow" size={17} />
                <span>Back</span>
              </button>
            </>
          )}
          <div className="breadcrumb">
            <span>FloodShield</span>
            <Icon name="chevron" size={15} />
            <b>{page}</b>
          </div>
          <div className="top-actions">
            <button
              className="icon-button notification"
              onClick={toggleNotifications}
              aria-label="Open notifications"
              aria-expanded={alerts}
            >
              <Icon name="bell" size={20} />
              {unreadNotifications > 0 && <i></i>}
            </button>
            <button
              className="profile-button"
              onClick={openAccount}
              aria-label={signedIn ? "Open profile" : "Open sign in"}
            >
              <Avatar profile={profileData} />
              <span>
                <b>{signedIn ? profileData.name : "Sign in"}</b>
                <small>
                  {signedIn ? profileData.role : "Access your workspace"}
                </small>
              </span>
              <Icon name="chevron" size={15} />
            </button>
          </div>
          {alerts && (
            <div className="alerts-popover" aria-live="polite">
              <div className="popover-title">
                <div>
                  <b>Notifications</b>
                  <span>
                    {unreadNotifications > 0
                      ? `${unreadNotifications} new`
                      : "All caught up"}
                  </span>
                </div>
                {unreadNotifications > 0 && (
                  <button
                    className="mark-read"
                    onClick={markAllNotificationsRead}
                  >
                    Mark all read
                  </button>
                )}
              </div>
              <div className="notification-list">
                {notifications.map((notification) => (
                  <Alert
                    key={notification.id}
                    {...notification}
                    onClick={() => markNotificationRead(notification.id)}
                  />
                ))}
              </div>
              <button
                onClick={() => {
                  setAlerts(false);
                  navigate("Risk intelligence");
                }}
              >
                Review risk intelligence <Icon name="arrow" size={16} />
              </button>
            </div>
          )}
        </header>
        <div className="page-container">
          {page === "Dashboard" && <Dashboard {...mainProps} />}
          {page === "Inventory" && <Inventory {...mainProps} />}
          {page === "Risk intelligence" && <Risk {...mainProps} />}
          {page === "Safe routes" && <Routes {...mainProps} />}
          {page === "Storage" && <Storage {...mainProps} />}
          {page === "Transport" && <Transport {...mainProps} />}
          {page === "Action plan" && <ActionPlan {...mainProps} />}
          {page === "Login" && (
            <LoginPage
              loginForm={loginForm}
              setLoginForm={setLoginForm}
              signIn={signIn}
            />
          )}
          {page === "Profile" && signedIn && (
            <ProfilePage
              profileData={profileData}
              setProfileData={setProfileData}
              signOut={signOut}
              flash={flash}
            />
          )}
        </div>
      </main>
      {modal && (
        <Modal
          modal={modal}
          close={() => setModal(null)}
          form={form}
          setForm={setForm}
          saveItem={saveItem}
          flash={flash}
        />
      )}
      {notice && (
        <div className="toast">
          <span>
            <Icon name="check" size={16} />
          </span>
          {notice}
        </div>
      )}
    </div>
  );
}

function Alert({ color, title, text, read = false, onClick }) {
  return (
    <button
      className={`alert-row ${read ? "is-read" : ""}`}
      onClick={onClick}
      type="button"
    >
      <i className={color}></i>
      <div>
        <b>{title}</b>
        <span>{text}</span>
      </div>
    </button>
  );
}
function Avatar({ profile, large = false }) {
  const initials =
    profile.name
      .split(" ")
      .filter(Boolean)
      .slice(0, 2)
      .map((part) => part[0])
      .join("")
      .toUpperCase() || "U";
  return (
    <span className={`avatar ${large ? "large" : ""}`}>
      {profile.photo ? (
        <img src={profile.photo} alt={`${profile.name}'s profile`} />
      ) : (
        initials
      )}
    </span>
  );
}
function Heading({ eyebrow, title, text, children }) {
  return (
    <section className="page-heading">
      <div>
        <p className="eyebrow">{eyebrow}</p>
        <h1>{title}</h1>
        <p className="subtitle">{text}</p>
      </div>
      {children && <div className="heading-actions">{children}</div>}
    </section>
  );
}
function PanelHead({ eyebrow, title, action, onClick }) {
  return (
    <div className="panel-head">
      <div>
        <p className="eyebrow">{eyebrow}</p>
        <h2>{title}</h2>
      </div>
      {action && (
        <button onClick={onClick}>
          {action}
          <Icon name="arrow" size={15} />
        </button>
      )}
    </div>
  );
}
function Button({
  kind = "primary",
  children,
  onClick,
  disabled = false,
  type = "button",
}) {
  return (
    <button
      type={type}
      className={`button ${kind}`}
      onClick={onClick}
      disabled={disabled}
    >
      {children}
    </button>
  );
}

function LoginPage({ loginForm, setLoginForm, signIn }) {
  return (
    <section className="login-page">
      <div className="login-intro">
        <p className="eyebrow">FLOODSHIELD WORKSPACE</p>
        <h1>Welcome back.</h1>
        <p>
          Sign in to manage your operational profile, alerts, and emergency
          response workspace.
        </p>
        <div className="login-feature-list">
          <span>
            <Icon name="shield" size={18} /> Secure account access
          </span>
          <span>
            <Icon name="user" size={18} /> Personalize your profile
          </span>
          <span>
            <Icon name="bell" size={18} /> Keep response alerts in one place
          </span>
        </div>
      </div>
      <form className="panel login-card" onSubmit={signIn}>
        <span className="account-icon">
          <Icon name="user" size={24} />
        </span>
        <p className="eyebrow">ACCOUNT ACCESS</p>
        <h2>Sign in to FloodShield</h2>
        <p>Use any valid email and a password of at least 6 characters.</p>
        <label>
          Email address
          <input
            type="email"
            autoComplete="email"
            autoFocus
            value={loginForm.email}
            onChange={(event) =>
              setLoginForm({ ...loginForm, email: event.target.value })
            }
            placeholder="you@example.com"
            required
          />
        </label>
        <label>
          Password
          <input
            type="password"
            autoComplete="current-password"
            minLength="6"
            value={loginForm.password}
            onChange={(event) =>
              setLoginForm({ ...loginForm, password: event.target.value })
            }
            placeholder="Enter your password"
            required
          />
        </label>
        <Button type="submit">
          Sign in <Icon name="arrow" size={16} />
        </Button>
        <small className="login-note">
          Demo mode: your profile is stored only while this page is open.
        </small>
      </form>
    </section>
  );
}

function ProfilePage({ profileData, setProfileData, signOut, flash }) {
  const [editing, setEditing] = useState(true);
  const [draft, setDraft] = useState(profileData);
  const updateDraft = (field, value) =>
    setDraft((current) => ({ ...current, [field]: value }));
  const startEditing = () => {
    setDraft(profileData);
    setEditing(true);
  };
  const cancelEditing = () => {
    setDraft(profileData);
    setEditing(false);
  };
  const choosePhoto = (event) => {
    const [file] = event.target.files;
    if (!file) return;
    if (file.size > 3 * 1024 * 1024) {
      flash("Please choose an image smaller than 3 MB.");
      return;
    }
    const reader = new FileReader();
    reader.onload = () => updateDraft("photo", String(reader.result));
    reader.readAsDataURL(file);
  };
  const saveProfile = (event) => {
    event.preventDefault();
    if (!draft.name.trim() || !draft.email.includes("@")) {
      flash("Add your name and a valid email address before saving.");
      return;
    }
    const updatedProfile = { ...draft, name: draft.name.trim() };
    setProfileData(updatedProfile);
    setDraft(updatedProfile);
    setEditing(false);
    flash("Your profile has been updated.");
  };

  return (
    <>
      <Heading
        eyebrow="ACCOUNT SETTINGS"
        title="Your profile"
        text="Manage the details that appear across your FloodShield workspace."
      >
        {!editing && (
          <Button onClick={startEditing}>
            <Icon name="edit" size={16} /> Edit profile
          </Button>
        )}
      </Heading>
      <section className="profile-layout">
        <aside className="panel profile-card">
          <div className="profile-avatar-wrap">
            <Avatar profile={editing ? draft : profileData} large />
            {editing && (
              <label className="photo-picker" title="Change profile photo">
                <Icon name="camera" size={16} />
                <input type="file" accept="image/*" onChange={choosePhoto} />
              </label>
            )}
          </div>
          <h2>{editing ? draft.name : profileData.name}</h2>
          <p>{editing ? draft.role : profileData.role}</p>
          <span className="account-active">
            <i></i> Account active
          </span>
          <div className="profile-card-actions">
            {editing ? (
              <Button kind="secondary" onClick={cancelEditing}>
                Cancel editing
              </Button>
            ) : (
              <Button kind="secondary" onClick={signOut}>
                <Icon name="logout" size={16} /> Sign out
              </Button>
            )}
          </div>
        </aside>
        <form className="panel profile-form" onSubmit={saveProfile}>
          <div className="profile-form-head">
            <div>
              <p className="eyebrow">PERSONAL DETAILS</p>
              <h2>{editing ? "Edit your profile" : "Profile details"}</h2>
            </div>
            {editing && <span className="editing-badge">Editing</span>}
          </div>
          <div className="profile-fields">
            <label>
              Full name
              <input
                value={editing ? draft.name : profileData.name}
                onChange={(event) => updateDraft("name", event.target.value)}
                disabled={!editing}
              />
            </label>
            <label>
              Role
              <input
                value={editing ? draft.role : profileData.role}
                onChange={(event) => updateDraft("role", event.target.value)}
                disabled={!editing}
              />
            </label>
            <label>
              Email address
              <input
                type="email"
                value={editing ? draft.email : profileData.email}
                onChange={(event) => updateDraft("email", event.target.value)}
                disabled={!editing}
              />
            </label>
            <label>
              Phone number
              <input
                type="tel"
                value={editing ? draft.phone : profileData.phone}
                onChange={(event) => updateDraft("phone", event.target.value)}
                disabled={!editing}
              />
            </label>
            <label>
              Organisation
              <input
                value={editing ? draft.organisation : profileData.organisation}
                onChange={(event) =>
                  updateDraft("organisation", event.target.value)
                }
                disabled={!editing}
              />
            </label>
            <label>
              Base location
              <input
                value={editing ? draft.location : profileData.location}
                onChange={(event) =>
                  updateDraft("location", event.target.value)
                }
                disabled={!editing}
              />
            </label>
          </div>
          {editing && (
            <footer className="profile-form-actions">
              <Button kind="secondary" onClick={cancelEditing}>
                Cancel
              </Button>
              <Button type="submit">
                <Icon name="check" size={16} /> Save changes
              </Button>
            </footer>
          )}
        </form>
      </section>
    </>
  );
}

function Dashboard({
  navigate,
  flash,
  setModal,
  highItems,
  totalValue,
  addItem,
  route,
  setRoute,
  profileData,
}) {
  return (
    <>
      <Heading
        eyebrow="SUNDAY, 23 AUGUST 2026"
        title={`Good afternoon, ${profileData.name.split(" ")[0] || "there"}.`}
        text="Here’s the latest readiness picture for your operation."
      >
        <Button kind="secondary" onClick={addItem}>
          <Icon name="plus" size={17} />
          Add inventory
        </Button>
        <Button onClick={() => navigate("Action plan")}>
          <Icon name="shield" size={17} />
          View action plan
        </Button>
      </Heading>
      <section className="critical-alert">
        <span>
          <Icon name="warning" size={22} />
        </span>
        <div>
          <b>Flood risk elevated for Riverside Depot</b>
          <p>
            Heavy rainfall is predicted this evening. Review your high-priority
            stock now.
          </p>
        </div>
        <button onClick={() => navigate("Risk intelligence")}>
          Review risk <Icon name="arrow" size={16} />
        </button>
      </section>
      <section className="metrics">
        <Metric
          icon="activity"
          label="Flood risk"
          value="HIGH"
          caption="Riverside zone"
          danger
          trend="↑ 18%"
        />
        <Metric
          icon="box"
          label="Priority stock"
          value={`${highItems.length} items`}
          caption="Require immediate action"
          click={() => navigate("Inventory")}
        />
        <Metric
          icon="warehouse"
          label="Safe storage"
          value="2 sites"
          caption="1,450 units available"
          click={() => navigate("Storage")}
        />
        <Metric
          icon="truck"
          label="Transport ready"
          value="4 vehicles"
          caption="Next departure 16:40"
          click={() => navigate("Transport")}
        />
      </section>
      <section className="dashboard-grid">
        <div className="panel risk-panel">
          <PanelHead
            eyebrow="RISK INTELLIGENCE"
            title="Flood impact snapshot"
            action="View details"
            onClick={() => navigate("Risk intelligence")}
          />
          <div className="risk-body">
            <div className="gauge-wrap">
              <div className="gauge">
                <i></i>
                <div>
                  <b>78</b>
                  <span>/ 100</span>
                </div>
              </div>
              <small>Risk score</small>
            </div>
            <div className="risk-details">
              <div>
                <span>Alert level</span>
                <b className="red-text">
                  <i></i>High
                </b>
              </div>
              <div>
                <span>Rainfall forecast</span>
                <b>
                  92 mm <small>next 6h</small>
                </b>
              </div>
              <div>
                <span>Peak flood window</span>
                <b>18:30 – 23:00</b>
              </div>
              <button onClick={() => navigate("Risk intelligence")}>
                Explore risk analysis <Icon name="arrow" size={15} />
              </button>
            </div>
          </div>
        </div>
        <div className="panel recommendation-panel">
          <PanelHead eyebrow="DECISION ENGINE" title="Recommended next steps" />
          <MiniAction
            type="move"
            icon="route"
            title="Move critical water filters"
            body="To North Hub before 17:45"
            button="Assign transport"
            onClick={() => navigate("Transport")}
          />
          <MiniAction
            type="protect"
            icon="shield"
            title="Protect dry supplies"
            body="Elevate 240 units at Riverside"
            button="View checklist"
            onClick={() => navigate("Action plan")}
          />
          <MiniAction
            type="sell"
            icon="arrow"
            title="Release surplus blankets"
            body="Safe to dispatch to nearby markets"
            button="Find buyers"
            onClick={() =>
              flash("Nearby market connections are ready to link.")
            }
          />
        </div>
      </section>
      <section className="dashboard-grid lower">
        <div className="panel route-panel">
          <PanelHead
            eyebrow="LOGISTICS"
            title="Safe route recommendation"
            action="All routes"
            onClick={() => navigate("Safe routes")}
          />
          <div className="route-visual">
            <div className="route-line"></div>
            <span className="route-dot start"></span>
            <span className="route-dot end"></span>
            <div className="route-label">
              <span>Riverside Depot</span>
              <span>North Hub</span>
            </div>
          </div>
          <div className="route-footer">
            <div>
              <b>{route}</b>
              <span>Low road risk · Traffic clear</span>
            </div>
            <div>
              <b>8.2 km</b>
              <span>22 mins</span>
            </div>
            <button
              className="icon-button"
              onClick={() =>
                setRoute(
                  route === "North Ring Road"
                    ? "Lake View Bypass"
                    : "North Ring Road",
                )
              }
            >
              <Icon name="route" size={18} />
            </button>
          </div>
        </div>
        <div className="panel priority-panel">
          <PanelHead
            eyebrow="INVENTORY"
            title="Priority items"
            action="Manage inventory"
            onClick={() => navigate("Inventory")}
          />
          <div className="priority-list">
            {highItems.slice(0, 3).map((item) => (
              <div className="priority-row" key={item.id}>
                <span className="item-icon">
                  <Icon name="box" size={17} />
                </span>
                <div>
                  <b>{item.name}</b>
                  <span>
                    {item.quantity} units · {item.location}
                  </span>
                </div>
                <em>{item.priority}</em>
              </div>
            ))}
          </div>
          <div className="priority-footer">
            <span>Protected value: ₹{totalValue.toLocaleString("en-IN")}</span>
            <button onClick={() => setModal("checklist")}>
              Review all <Icon name="arrow" size={15} />
            </button>
          </div>
        </div>
      </section>
    </>
  );
}
function Metric({ icon, label, value, caption, danger, trend, click }) {
  return (
    <article className={`metric ${danger ? "danger" : ""}`}>
      <span className="metric-icon">
        <Icon name={icon} size={20} />
      </span>
      <div className="metric-label">
        <span>{label}</span>
        {trend ? (
          <b>{trend}</b>
        ) : (
          <button onClick={click}>
            <Icon name="arrow" size={15} />
          </button>
        )}
      </div>
      <strong>{value}</strong>
      <small>{caption}</small>
    </article>
  );
}
function MiniAction({ type, icon, title, body, button, onClick }) {
  return (
    <div className="mini-action">
      <span className={type}>
        <Icon name={icon} size={19} />
      </span>
      <div>
        <b>{title}</b>
        <small>{body}</small>
        <button onClick={onClick}>
          {button}
          <Icon name="arrow" size={14} />
        </button>
      </div>
    </div>
  );
}

function Inventory({
  addItem,
  navigate,
  flash,
  filtered,
  items,
  search,
  setSearch,
  removeItem,
}) {
  return (
    <>
      <Heading
        eyebrow="SUPPLY READINESS"
        title="Inventory control"
        text="Add, track, and prioritize supplies before conditions change."
      >
        <Button
          kind="secondary"
          onClick={() => {
            navigate("Risk intelligence");
            flash("Inventory risk analysis refreshed.");
          }}
        >
          <Icon name="activity" size={17} />
          Run analysis
        </Button>
        <Button onClick={addItem}>
          <Icon name="plus" size={17} />
          Add inventory
        </Button>
      </Heading>
      <section className="inventory-summary">
        <Stat label="Total tracked items" value={items.length} />
        <Stat label="At high flood risk" value="2 items" red />
        <Stat label="Estimated value at risk" value="₹2.58L" />
        <Stat label="Last assessment" value="Just now" />
      </section>
      <section className="panel inventory-table">
        <div className="table-toolbar">
          <div>
            <h2>Available stock</h2>
            <span>Live inventory across 2 locations</span>
          </div>
          <label className="search">
            <Icon name="search" size={17} />
            <input
              value={search}
              onChange={(event) => setSearch(event.target.value)}
              placeholder="Search inventory"
            />
          </label>
        </div>
        <div className="table-scroll">
          <table>
            <thead>
              <tr>
                <th>Item</th>
                <th>Location</th>
                <th>Quantity</th>
                <th>Value</th>
                <th>Priority</th>
                <th>Risk</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((item) => (
                <tr key={item.id}>
                  <td>
                    <div className="table-item">
                      <span className="item-icon">
                        <Icon name="box" size={17} />
                      </span>
                      <div>
                        <b>{item.name}</b>
                        <small>{item.category}</small>
                      </div>
                    </div>
                  </td>
                  <td>{item.location}</td>
                  <td>{item.quantity} units</td>
                  <td>₹{item.value.toLocaleString("en-IN")}</td>
                  <td>
                    <i className="score">
                      <i style={{ width: `${item.priority}%` }}></i>
                    </i>
                    {item.priority}
                  </td>
                  <td>
                    <span className={`pill ${item.risk.toLowerCase()}`}>
                      <i></i>
                      {item.risk}
                    </span>
                  </td>
                  <td>
                    <button
                      className="delete"
                      onClick={() => removeItem(item.id)}
                      aria-label={`Remove ${item.name}`}
                    >
                      <Icon name="trash" size={16} />
                    </button>
                  </td>
                </tr>
              ))}
              {filtered.length === 0 && (
                <tr>
                  <td colSpan="7" className="empty">
                    No inventory matches your search.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </section>
    </>
  );
}
function Stat({ label, value, red }) {
  return (
    <div>
      <span>{label}</span>
      <b className={red ? "red-text" : ""}>{value}</b>
    </div>
  );
}

function Risk({ navigate, flash, items }) {
  const high = items.filter((item) => item.risk === "High").length;
  return (
    <>
      <Heading
        eyebrow="AI-POWERED RISK ENGINE"
        title="Risk intelligence"
        text="Live flood impact analysis for your sites, supplies, and operations."
      >
        <Button
          onClick={() =>
            flash("Risk assessment updated with the latest forecast.")
          }
        >
          <Icon name="activity" size={17} />
          Refresh analysis
        </Button>
      </Heading>
      <section className="risk-page">
        <div className="panel flood-map">
          <div className="map-head">
            <div>
              <p className="eyebrow">LIVE RISK MAP</p>
              <h2>Riverside operational area</h2>
            </div>
            <span>● Live data</span>
          </div>
          <div className="map">
            <i className="water a"></i>
            <i className="water b"></i>
            <i className="road a"></i>
            <i className="road b"></i>
            <div className="map-tag depot">
              ● Riverside Depot <b>High risk</b>
            </div>
            <div className="map-tag hub">
              ● North Hub <b>Safe</b>
            </div>
            <div className="map-legend">
              <span>● High</span>
              <span>● Medium</span>
              <span>● Low</span>
            </div>
          </div>
        </div>
        <aside className="panel assessment">
          <p className="eyebrow">CURRENT ASSESSMENT</p>
          <div className="assessment-head">
            <b>
              78<small>/100</small>
            </b>
            <div>
              <span>Flood risk level</span>
              <h2 className="red-text">High</h2>
              <small>Action required before 18:30</small>
            </div>
          </div>
          <div className="assessment-list">
            <span>
              Flood probability<b>84%</b>
            </span>
            <span>
              Expected water level<b>1.2 m</b>
            </span>
            <span>
              High-priority items<b>{high} items</b>
            </span>
          </div>
          <Button onClick={() => navigate("Action plan")}>
            <Icon name="clipboard" size={17} />
            Open recommended plan
          </Button>
        </aside>
      </section>
      <section className="panel timeline">
        <PanelHead eyebrow="FORECAST WINDOW" title="Water-level prediction" />
        <div className="chart">
          <div className="critical-line">Critical level</div>
          <svg viewBox="0 0 720 170" preserveAspectRatio="none">
            <defs>
              <linearGradient id="flood" x1="0" x2="0" y1="0" y2="1">
                <stop stopColor="#d65252" stopOpacity=".35" />
                <stop offset="1" stopColor="#d65252" stopOpacity="0" />
              </linearGradient>
            </defs>
            <path
              d="M0,150 C70,148 80,132 135,128 S200,116 240,120 S320,95 370,75 S435,52 485,65 S570,28 625,35 S680,65 720,80 V170 H0Z"
              fill="url(#flood)"
            />
            <path
              d="M0,150 C70,148 80,132 135,128 S200,116 240,120 S320,95 370,75 S435,52 485,65 S570,28 625,35 S680,65 720,80"
              fill="none"
              stroke="#ed7777"
              strokeWidth="3"
            />
          </svg>
          <div className="x-labels">
            <span>12:00</span>
            <span>15:00</span>
            <span>18:00</span>
            <span>21:00</span>
            <span>00:00</span>
          </div>
        </div>
      </section>
    </>
  );
}

function Routes({ route, setRoute, flash }) {
  const routes = [
    {
      name: "North Ring Road",
      time: "22 min",
      distance: "8.2 km",
      risk: "Low",
      note: "Clear traffic · Avoids flood zone",
      recommended: true,
    },
    {
      name: "Lake View Bypass",
      time: "28 min",
      distance: "10.4 km",
      risk: "Low",
      note: "Clear route · Light traffic",
    },
    {
      name: "Main Market Road",
      time: "18 min",
      distance: "6.9 km",
      risk: "High",
      note: "Waterlogging reported near Junction 6",
    },
  ];
  return (
    <>
      <Heading
        eyebrow="LOGISTICS LAYER"
        title="Safe route selection"
        text="Move critical supplies through routes assessed for flood and road risk."
      >
        <Button
          kind="secondary"
          onClick={() =>
            flash("Route conditions refreshed from live traffic data.")
          }
        >
          <Icon name="route" size={17} />
          Refresh routes
        </Button>
      </Heading>
      <section className="routes-page">
        <div className="panel route-list">
          <PanelHead
            eyebrow="RIVERSIDE DEPOT → NORTH HUB"
            title="Available routes"
          />
          {routes.map((item) => (
            <button
              className={`route-choice ${route === item.name ? "selected" : ""}`}
              key={item.name}
              onClick={() => setRoute(item.name)}
            >
              <i></i>
              <div>
                <b>
                  {item.name}
                  {item.recommended && <em>Recommended</em>}
                </b>
                <small>{item.note}</small>
                <span className={`pill ${item.risk.toLowerCase()}`}>
                  <i></i>
                  {item.risk} road risk
                </span>
              </div>
              <aside>
                <b>{item.time}</b>
                <small>{item.distance}</small>
              </aside>
            </button>
          ))}
        </div>
        <div className="panel route-detail">
          <p className="eyebrow">SELECTED ROUTE</p>
          <h2>{route}</h2>
          <div className="route-map">
            <i></i>
            <span className="source">⌂</span>
            <span className="destination">⌂</span>
            <b>8.2 km · 22 min</b>
          </div>
          <div className="route-stats">
            <span>
              <Icon name="clock" size={18} />
              Estimated time<b>22 minutes</b>
            </span>
            <span>
              <Icon name="shield" size={18} />
              Road risk<b className="green-text">Low</b>
            </span>
          </div>
          <Button
            onClick={() => {
              window.open(
                "https://www.google.com/maps/dir/",
                "_blank",
                "noopener,noreferrer",
              );
              flash("Opening your selected safe route.");
            }}
          >
            <Icon name="external" size={17} />
            Open navigation
          </Button>
        </div>
      </section>
    </>
  );
}

function Storage({ setModal }) {
  const locations = [
    {
      name: "North Hub",
      place: "Sector 12, North District",
      capacity: 72,
      available: "780 units",
      status: "Recommended",
      distance: "8.2 km away",
    },
    {
      name: "Central Relief Store",
      place: "Town Centre",
      capacity: 54,
      available: "430 units",
      status: "Available",
      distance: "4.7 km away",
    },
    {
      name: "West Logistics Yard",
      place: "Industrial Estate",
      capacity: 88,
      available: "240 units",
      status: "Available",
      distance: "12.6 km away",
    },
  ];
  return (
    <>
      <Heading
        eyebrow="SAFE STORAGE NETWORK"
        title="Storage availability"
        text="Secure inventory at verified facilities outside the flood impact zone."
      >
        <Button onClick={() => setModal("storage")}>
          <Icon name="plus" size={17} />
          Add warehouse
        </Button>
      </Heading>
      <section className="storage-summary">
        <div>
          <Icon name="warehouse" size={21} />
          <span>
            Safe capacity available<b>1,450 units</b>
          </span>
        </div>
        <div>
          <Icon name="shield" size={21} />
          <span>
            Verified flood-safe sites<b>3 locations</b>
          </span>
        </div>
        <div>
          <Icon name="route" size={21} />
          <span>
            Closest safe facility<b>4.7 km away</b>
          </span>
        </div>
      </section>
      <section className="warehouse-grid">
        {locations.map((item) => (
          <article className="panel warehouse" key={item.name}>
            <div className="warehouse-top">
              <span>
                <Icon name="warehouse" size={21} />
              </span>
              <em
                className={item.status === "Recommended" ? "recommended" : ""}
              >
                {item.status}
              </em>
            </div>
            <h2>{item.name}</h2>
            <p>
              <Icon name="location" size={15} />
              {item.place}
            </p>
            <div className="capacity">
              <div>
                <span>Current capacity</span>
                <b>{item.capacity}% used</b>
              </div>
              <i>
                <i style={{ width: `${item.capacity}%` }}></i>
              </i>
              <small>{item.available} space available</small>
            </div>
            <footer>
              <span>{item.distance}</span>
              <button
                onClick={() => setModal({ type: "booking", name: item.name })}
              >
                Reserve space <Icon name="arrow" size={15} />
              </button>
            </footer>
          </article>
        ))}
      </section>
    </>
  );
}

function Transport({ flash, setModal }) {
  const trucks = [
    {
      name: "Truck 01",
      type: "Medium cargo",
      capacity: "1.5 t",
      location: "Riverside Depot",
      eta: "Ready now",
      busy: false,
    },
    {
      name: "Truck 03",
      type: "Heavy cargo",
      capacity: "3.0 t",
      location: "North Hub",
      eta: "Ready in 25 min",
      busy: false,
    },
    {
      name: "Van 02",
      type: "Light cargo",
      capacity: "700 kg",
      location: "Central Store",
      eta: "On delivery",
      busy: true,
    },
  ];
  return (
    <>
      <Heading
        eyebrow="TRANSPORT MATCHING"
        title="Transport readiness"
        text="Assign available vehicles to move priority supplies safely and on time."
      >
        <Button onClick={() => setModal("transport")}>
          <Icon name="plus" size={17} />
          Add vehicle
        </Button>
      </Heading>
      <section className="transport-callout">
        <div>
          <p className="eyebrow">NEXT RECOMMENDED MOVE</p>
          <h2>Move water filters to North Hub</h2>
          <p>85 units · 8.2 km · Target arrival before 17:45</p>
        </div>
        <Button
          kind="light"
          onClick={() => flash("Truck 01 has been assigned to this movement.")}
        >
          Assign Truck 01 <Icon name="arrow" size={16} />
        </Button>
      </section>
      <section className="vehicle-grid">
        {trucks.map((item) => (
          <article className="panel vehicle" key={item.name}>
            <span className="truck-icon">
              <Icon name="truck" size={25} />
            </span>
            <div className="vehicle-name">
              <div>
                <h2>{item.name}</h2>
                <p>
                  {item.type} · {item.capacity}
                </p>
              </div>
              <span className={`pill ${item.busy ? "medium" : "low"}`}>
                <i></i>
                {item.busy ? "In transit" : "Ready"}
              </span>
            </div>
            <div className="vehicle-data">
              <span>
                Current location<b>{item.location}</b>
              </span>
              <span>
                Availability<b>{item.eta}</b>
              </span>
            </div>
            <Button
              kind="secondary"
              disabled={item.busy}
              onClick={() => flash(`${item.name} assigned to selected route.`)}
            >
              {item.busy ? "Currently in transit" : "Assign vehicle"}{" "}
              <Icon name="arrow" size={16} />
            </Button>
          </article>
        ))}
      </section>
    </>
  );
}

function ActionPlan({ done, setDone, exportPlan, flash }) {
  const toggle = (id) =>
    setDone((current) =>
      current.includes(id)
        ? current.filter((task) => task !== id)
        : [...current, id],
    );
  return (
    <>
      <Heading
        eyebrow="YOUR EMERGENCY RESPONSE"
        title="Action plan"
        text="A prioritized plan created from flood risk, stock value, and logistics availability."
      >
        <Button kind="secondary" onClick={exportPlan}>
          <Icon name="download" size={17} />
          Export plan
        </Button>
        <Button
          onClick={() =>
            flash("Action plan has been shared with your operations team.")
          }
        >
          <Icon name="external" size={17} />
          Share plan
        </Button>
      </Heading>
      <section className="plan-status">
        <span>
          <Icon name="shield" size={26} />
        </span>
        <div>
          <p className="eyebrow">FLOODSHIELD RECOMMENDATION</p>
          <h2>Secure high-priority supplies before the flood window.</h2>
          <p>
            We found 3 actions that can reduce your estimated exposure by
            ₹85,000.
          </p>
        </div>
        <aside>
          <b>{done.length} / 3</b>
          <span>actions complete</span>
          <i>
            <i style={{ width: `${(done.length / 3) * 100}%` }}></i>
          </i>
        </aside>
      </section>
      <section className="action-grid">
        <div>
          {planTasks.map((task) => (
            <article
              className={`task ${done.includes(task.id) ? "done" : ""}`}
              key={task.id}
            >
              <button
                onClick={() => toggle(task.id)}
                aria-label={`Complete ${task.title}`}
              >
                <Icon name="check" size={16} />
              </button>
              <div>
                <span>{task.time}</span>
                <h2>{task.title}</h2>
                <p>{task.detail}</p>
                <button
                  onClick={() => {
                    toggle(task.id);
                    flash("Action status updated.");
                  }}
                >
                  {done.includes(task.id)
                    ? "Mark incomplete"
                    : "Mark as complete"}
                  <Icon name="arrow" size={15} />
                </button>
              </div>
            </article>
          ))}
        </div>
        <aside className="panel impact">
          <p className="eyebrow">IMPACT SUMMARY</p>
          <span>
            Flood risk<b className="red-text">High</b>
          </span>
          <span>
            Priority stock<b>₹2.58L</b>
          </span>
          <span>
            Safe route<b>North Ring Road</b>
          </span>
          <span>
            Recommended vehicle<b>Truck 01</b>
          </span>
          <hr />
          <div>
            <small>Estimated exposure reduction</small>
            <b>₹85,000</b>
          </div>
          <Button onClick={() => flash("Response team has been notified.")}>
            <Icon name="bell" size={17} />
            Notify response team
          </Button>
        </aside>
      </section>
    </>
  );
}

function Modal({ modal, close, form, setForm, saveItem, flash }) {
  const title =
    modal === "help"
      ? "Emergency help center"
      : modal === "storage"
        ? "Add a warehouse"
        : modal === "transport"
          ? "Add a vehicle"
          : modal === "checklist"
            ? "Priority item checklist"
            : `Reserve at ${modal.name}`;
  if (modal !== "inventory")
    return (
      <div className="modal-backdrop">
        <div className="modal simple">
          <button className="modal-close" onClick={close}>
            <Icon name="close" />
          </button>
          <span>
            <Icon
              name={
                modal === "help"
                  ? "warning"
                  : modal === "transport"
                    ? "truck"
                    : "warehouse"
              }
              size={25}
            />
          </span>
          <h2>{title}</h2>
          <p>
            {modal === "help"
              ? "For immediate danger, call the national emergency number 112. You can also share your live location with local response teams."
              : "This interactive demo is ready to connect to your backend endpoint for creating or reserving logistics resources."}
          </p>
          <Button
            onClick={() => {
              close();
              flash("Request recorded successfully.");
            }}
          >
            Continue <Icon name="arrow" size={16} />
          </Button>
        </div>
      </div>
    );
  return (
    <div className="modal-backdrop">
      <form className="modal inventory-modal" onSubmit={saveItem}>
        <button type="button" className="modal-close" onClick={close}>
          <Icon name="close" />
        </button>
        <p className="eyebrow">INVENTORY INTAKE</p>
        <h2>Add inventory item</h2>
        <p>The item will be included in risk and priority analysis.</p>
        <label>
          Item name
          <input
            autoFocus
            value={form.name}
            onChange={(event) => setForm({ ...form, name: event.target.value })}
            placeholder="e.g. Portable water filters"
          />
        </label>
        <div className="form-row">
          <label>
            Category
            <select
              value={form.category}
              onChange={(event) =>
                setForm({ ...form, category: event.target.value })
              }
            >
              <option>Essential food</option>
              <option>Medical supplies</option>
              <option>Relief equipment</option>
              <option>Other</option>
            </select>
          </label>
          <label>
            Location
            <select
              value={form.location}
              onChange={(event) =>
                setForm({ ...form, location: event.target.value })
              }
            >
              <option>Riverside Depot</option>
              <option>Central Store</option>
              <option>North Hub</option>
            </select>
          </label>
        </div>
        <div className="form-row">
          <label>
            Quantity
            <input
              type="number"
              min="1"
              value={form.quantity}
              onChange={(event) =>
                setForm({ ...form, quantity: event.target.value })
              }
              placeholder="0"
            />
          </label>
          <label>
            Estimated value (₹)
            <input
              type="number"
              min="1"
              value={form.value}
              onChange={(event) =>
                setForm({ ...form, value: event.target.value })
              }
              placeholder="0"
            />
          </label>
        </div>
        <footer>
          <Button kind="secondary" onClick={close}>
            Cancel
          </Button>
          <Button type="submit">
            <Icon name="plus" size={16} />
            Add to analysis
          </Button>
        </footer>
      </form>
    </div>
  );
}

export default App;

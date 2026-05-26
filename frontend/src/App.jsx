import { useState, useEffect } from "react";
import "./App.css";

const API = "http://localhost:8000";

// ==========================================
// 导航栏组件
// ==========================================
function Nav({ token, onNavigate, onFetchAttractions, onFetchBookmarks, onLogout }) {
  return (
    <nav className="nav">
      <div className="nav-brand" onClick={() => onNavigate("home")}>
        旅游收藏夹
      </div>
      <div className="nav-links">
        <button onClick={() => { onNavigate("home"); onFetchAttractions(); }}>
          景点列表
        </button>
        {token && (
          <button onClick={() => { onNavigate("bookmarks"); onFetchBookmarks(); }}>
            我的收藏
          </button>
        )}
        {token ? (
          <button onClick={onLogout}>退出登录</button>
        ) : (
          <>
            <button onClick={() => onNavigate("login")}>登录</button>
            <button onClick={() => onNavigate("register")}>注册</button>
          </>
        )}
      </div>
    </nav>
  );
}

// ==========================================
// 景点列表组件
// ==========================================
function AttractionList({ attractions, attractionCount, skip, limit, token, onAddBookmark, onFetch }) {
  const [filterSearch, setFilterSearch] = useState("");
  const [filterCity, setFilterCity] = useState("");
  const [filterType, setFilterType] = useState("");

  function search() {
    onFetch({ skip: 0, search: filterSearch, city: "", type: "" });
    setFilterCity("");
    setFilterType("");
  }

  function selectCity(value) {
    setFilterCity(value);
    setFilterType("");
    setFilterSearch("");
    if (value) onFetch({ skip: 0, city: value, type: "", search: "", mode: "city" });
    else onFetch({ skip: 0, city: "", type: "", search: "" });
  }

  function selectType(value) {
    setFilterType(value);
    setFilterCity("");
    setFilterSearch("");
    if (value) onFetch({ skip: 0, city: "", type: value, search: "", mode: "type" });
    else onFetch({ skip: 0, city: "", type: "", search: "" });
  }

  function goPage(newSkip) {
    onFetch({ skip: newSkip, city: filterCity, type: filterType, search: filterSearch });
    window.scrollTo({ top: 0, behavior: "smooth" });
  }

  return (
    <div className="page">
      <h2>景点列表</h2>

      <div className="filter-bar">
        <input
          type="text"
          placeholder="搜索景点或城市..."
          value={filterSearch}
          onChange={(e) => setFilterSearch(e.target.value)}
          onKeyDown={(e) => { if (e.key === "Enter") search(); }}
        />
        <button onClick={search}>搜索</button>
        <select value={filterCity} onChange={(e) => selectCity(e.target.value)}>
          <option value="">全部城市</option>
          <option value="北京">北京</option>
          <option value="上海">上海</option>
          <option value="广州">广州</option>
          <option value="深圳">深圳</option>
          <option value="杭州">杭州</option>
          <option value="成都">成都</option>
        </select>
        <select value={filterType} onChange={(e) => selectType(e.target.value)}>
          <option value="">全部类型</option>
          <option value="自然风光">自然风光</option>
          <option value="历史遗迹">历史遗迹</option>
          <option value="主题公园">主题公园</option>
          <option value="博物馆">博物馆</option>
          <option value="商业街区">商业街区</option>
        </select>
      </div>

      <p className="count-info">共 {attractionCount} 个景点</p>

      {attractions.length === 0 ? (
        <p className="empty">暂无景点数据，请先导入数据</p>
      ) : (
        <div className="card-list">
          {attractions.map((a) => (
            <div className="card" key={a.id || a.attraction_id}>
              <h3>{a.attraction_name}</h3>
              <p className="card-meta">
                <span>{a.city_name}</span>
                {a.type && <span className="tag">{a.type}</span>}
                {a.ticket_price != null && <span className="price">¥{a.ticket_price}</span>}
              </p>
              {a.overview && (
                <p className="card-desc">
                  {(a.overview || "").slice(0, 120)}
                  {(a.overview || "").length > 120 ? "..." : ""}
                </p>
              )}
              <p className="card-info">
                {a.open_hours && <span>开放: {a.open_hours}</span>}
                {a.duration_of_visit && <span>建议游览: {a.duration_of_visit}</span>}
              </p>
              {token && (
                <button className="btn-bookmark" onClick={() => onAddBookmark(a.attraction_id)}>
                  收藏
                </button>
              )}
            </div>
          ))}
        </div>
      )}

      {attractionCount > limit && (
        <div className="pagination">
          <button disabled={skip === 0} onClick={() => goPage(Math.max(0, skip - limit))}>
            上一页
          </button>
          <span>第 {Math.floor(skip / limit) + 1} / {Math.ceil(attractionCount / limit)} 页</span>
          <button
            disabled={skip + limit >= attractionCount}
            onClick={() => goPage(skip + limit)}
          >
            下一页
          </button>
        </div>
      )}
    </div>
  );
}

// ==========================================
// 登录页组件
// ==========================================
function LoginPage({ msg, onLogin }) {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  return (
    <div className="page form-page">
      <h2>用户登录</h2>
      {msg && <p className="msg">{msg}</p>}
      <input type="email" placeholder="邮箱" value={email} onChange={(e) => setEmail(e.target.value)} />
      <input type="password" placeholder="密码" value={password} onChange={(e) => setPassword(e.target.value)} />
      <button className="btn-primary" onClick={() => onLogin(email, password)}>登录</button>
    </div>
  );
}

// ==========================================
// 注册页组件
// ==========================================
function RegisterPage({ msg, onRegister }) {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [name, setName] = useState("");

  function submit() {
    onRegister(email, password, name);
    setEmail("");
    setPassword("");
    setName("");
  }

  return (
    <div className="page form-page">
      <h2>用户注册</h2>
      {msg && <p className="msg">{msg}</p>}
      <input type="email" placeholder="邮箱" value={email} onChange={(e) => setEmail(e.target.value)} />
      <input type="password" placeholder="密码（至少8位）" value={password} onChange={(e) => setPassword(e.target.value)} />
      <input type="text" placeholder="姓名（选填）" value={name} onChange={(e) => setName(e.target.value)} />
      <button className="btn-primary" onClick={submit}>注册</button>
    </div>
  );
}

// ==========================================
// 收藏列表组件
// ==========================================
function BookmarkList({ bookmarks, onRemove }) {
  return (
    <div className="page">
      <h2>我的收藏</h2>
      {bookmarks.length === 0 ? (
        <p className="empty">暂无收藏</p>
      ) : (
        <div className="card-list">
          {bookmarks.map((b) => (
            <div className="card" key={b.id}>
              <h3>景点 #{b.attraction_id}</h3>
              <p className="card-meta">收藏时间: {b.created_at}</p>
              <button className="btn-bookmark danger" onClick={() => onRemove(b.attraction_id)}>
                取消收藏
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

// ==========================================
// 主应用入口
// ==========================================
export default function App() {
  const [page, setPage] = useState("home");
  const [token, setToken] = useState(localStorage.getItem("token") || "");
  const [msg, setMsg] = useState("");

  // 景点
  const [attractions, setAttractions] = useState([]);
  const [attractionCount, setAttractionCount] = useState(0);
  const [skip, setSkip] = useState(0);
  const limit = 10;

  // 收藏
  const [bookmarks, setBookmarks] = useState([]);

  function headers() {
    const h = { "Content-Type": "application/json" };
    if (token) h["Authorization"] = `Bearer ${token}`;
    return h;
  }

  async function fetchAttractions(opts = {}) {
    try {
      const s = opts.skip ?? 0;
      const l = opts.limit ?? limit;
      const params = new URLSearchParams({ skip: s, limit: l });
      if (opts.city) params.append("city", opts.city);
      if (opts.type) params.append("type", opts.type);
      if (opts.search) params.append("search", opts.search);

      let res;
      if (opts.mode === "city" && opts.city) {
        res = await fetch(`${API}/api/attractions/city/${encodeURIComponent(opts.city)}?${params}`);
      } else if (opts.mode === "type" && opts.type) {
        res = await fetch(`${API}/api/attractions/type/${encodeURIComponent(opts.type)}?${params}`);
      } else {
        res = await fetch(`${API}/api/attractions?${params}`);
      }

      const data = await res.json();
      if (res.ok) {
        setAttractions(data.data || []);
        setAttractionCount(data.count || 0);
        setSkip(s);
      }
    } catch (e) {
      console.error("获取景点失败", e);
    }
  }

  async function fetchBookmarks() {
    try {
      const params = new URLSearchParams({ skip: 0, limit: 100 });
      const res = await fetch(`${API}/api/bookmarks?${params}`, { headers: headers() });
      const data = await res.json();
      if (res.ok) setBookmarks(data.data || []);
    } catch (_) {}
  }

  async function login(email, password) {
    try {
      const res = await fetch(`${API}/api/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password }),
      });
      const data = await res.json();
      if (!res.ok) { setMsg(data.detail || "登录失败"); return; }
      localStorage.setItem("token", data.access_token);
      setToken(data.access_token);
      setMsg("登录成功");
      setPage("home");
    } catch (e) {
      setMsg("网络错误: " + e.message);
    }
  }

  async function register(email, password, full_name) {
    try {
      const res = await fetch(`${API}/api/register`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password, full_name: full_name || null }),
      });
      const data = await res.json();
      if (!res.ok) { setMsg(data.detail || "注册失败"); return; }
      setMsg("注册成功，请登录");
      setPage("login");
    } catch (e) {
      setMsg("网络错误: " + e.message);
    }
  }

  function logout() {
    localStorage.removeItem("token");
    setToken("");
    setPage("home");
  }

  async function addBookmark(attractionId) {
    try {
      const res = await fetch(`${API}/api/bookmarks/${attractionId}`, {
        method: "POST", headers: headers(),
      });
      const data = await res.json();
      setMsg(res.ok ? "收藏成功" : (data.detail || "收藏失败"));
      if (res.ok) fetchBookmarks();
    } catch (e) {
      setMsg("网络错误: " + e.message);
    }
  }

  async function removeBookmark(attractionId) {
    try {
      const res = await fetch(`${API}/api/bookmarks/${attractionId}`, {
        method: "DELETE", headers: headers(),
      });
      const data = await res.json();
      setMsg(res.ok ? "取消收藏成功" : (data.detail || "取消收藏失败"));
      if (res.ok) fetchBookmarks();
    } catch (e) {
      setMsg("网络错误: " + e.message);
    }
  }

  useEffect(() => {
    fetchAttractions();
  }, []);

  function renderPage() {
    switch (page) {
      case "login":
        return <LoginPage msg={msg} onLogin={login} />;
      case "register":
        return <RegisterPage msg={msg} onRegister={register} />;
      case "bookmarks":
        return <BookmarkList bookmarks={bookmarks} onRemove={removeBookmark} />;
      default:
        return (
          <AttractionList
            attractions={attractions}
            attractionCount={attractionCount}
            skip={skip}
            limit={limit}
            token={token}
            onAddBookmark={addBookmark}
            onFetch={fetchAttractions}
          />
        );
    }
  }

  return (
    <div className="app">
      <Nav
        token={token}
        onNavigate={setPage}
        onFetchAttractions={fetchAttractions}
        onFetchBookmarks={fetchBookmarks}
        onLogout={logout}
      />
      {msg && page !== "login" && page !== "register" && (
        <p className="msg-top" onClick={() => setMsg("")}>{msg}</p>
      )}
      {renderPage()}
    </div>
  );
}

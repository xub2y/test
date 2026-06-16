import React, { useState } from 'react';
import axios from 'axios';
import { useNavigate } from 'react-router-dom';
import './Form.css';

function Login() {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [message, setMessage] = useState('');
  const navigate = useNavigate();

  const handleLogin = async () => {
    if (!username) { setMessage('用户名不能为空'); return; }
    if (!password) { setMessage('密码不能为空'); return; }
    try {
      const res = await axios.post('http://127.0.0.1:5000/api/login', { username, password });
      localStorage.setItem('token', res.data.token);
      localStorage.setItem('username', res.data.username);
      navigate('/home');
    } catch (err) {
      setMessage(err.response?.data?.error || '登录失败');
    }
  };

  return (
    <div className="form-container">
      <div className="form-box">
        <h2>用户登录</h2>
        <input type="text" placeholder="请输入用户名" value={username} onChange={e => setUsername(e.target.value)} />
        <input type="password" placeholder="请输入密码" value={password} onChange={e => setPassword(e.target.value)} />
        <button onClick={handleLogin}>登录</button>
        {message && <p className="error">{message}</p>}
        <p className="link" onClick={() => navigate('/register')}>没有账号？去注册</p>
      </div>
    </div>
  );
}

export default Login;

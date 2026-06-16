import React, { useState } from 'react';
import axios from 'axios';
import { useNavigate } from 'react-router-dom';
import './Form.css';

function Register() {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [message, setMessage] = useState('');
  const [isError, setIsError] = useState(false);
  const navigate = useNavigate();

  const handleRegister = async () => {
    if (!username) { setIsError(true); setMessage('用户名不能为空'); return; }
    if (!password) { setIsError(true); setMessage('密码不能为空'); return; }
    try {
      const res = await axios.post('http://127.0.0.1:5000/api/register', { username, password });
      setIsError(false);
      setMessage(res.data.message);
      setTimeout(() => navigate('/login'), 1500);
    } catch (err) {
      setIsError(true);
      setMessage(err.response?.data?.error || '注册失败');
    }
  };

  return (
    <div className="form-container">
      <div className="form-box">
        <h2>用户注册</h2>
        <input type="text" placeholder="请输入用户名（6-20位）" value={username} onChange={e => setUsername(e.target.value)} />
        <input type="password" placeholder="请输入密码（6-30位）" value={password} onChange={e => setPassword(e.target.value)} />
        <button onClick={handleRegister}>注册</button>
        {message && <p className={isError ? 'error' : 'success'}>{message}</p>}
        <p className="link" onClick={() => navigate('/login')}>已有账号？去登录</p>
      </div>
    </div>
  );
}

export default Register;

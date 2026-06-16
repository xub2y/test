import React from 'react';
import { useNavigate } from 'react-router-dom';
import './Form.css';

function Home() {
  const navigate = useNavigate();
  const username = localStorage.getItem('username') || '用户';

  const handleLogout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('username');
    navigate('/login');
  };

  return (
    <div className="form-container">
      <div className="form-box">
        <h2>欢迎回来，{username}！</h2>
        <p style={{color:'#666', marginBottom:'24px'}}>您已成功登录系统</p>
        <button onClick={handleLogout}>退出登录</button>
      </div>
    </div>
  );
}

export default Home;

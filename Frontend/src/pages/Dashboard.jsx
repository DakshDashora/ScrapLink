import { useSelector } from 'react-redux';

const Dashboard = () => {
  const user = useSelector((state) => state.auth.user);
  return (
    <div className="dashboard-home">
      <h2>Dashboard</h2>
      <p>Welcome back, {user?.full_name}!</p>
      <p>Email: {user?.email} {user?.email_verified ? '(verified)' : '(not verified)'}</p>
      <p>Phone: {user?.phone} {user?.phone_verified ? '(verified)' : '(not verified)'}</p>
      <p>Role: {user?.role}</p>
    </div>
  );
};

export default Dashboard;
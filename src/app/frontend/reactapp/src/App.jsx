
import { BrowserRouter as Router, Route, Routes } from 'react-router-dom';
import Chart from 'chart.js/auto';
function App() {
  return (
    <Router>
      <Routes>
        <Route path='/' element={<Dashboard />} />
        <Route path='/login' element={<Login />} />
      </Routes>
    </Router>
  );
}

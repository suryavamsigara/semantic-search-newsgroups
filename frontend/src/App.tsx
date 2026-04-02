import './App.css'
import SearchPage from './SearchPage'
import DocumentPage from './DocumentPage'
import { BrowserRouter, Routes, Route } from 'react-router-dom'

function App() {

  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<SearchPage />} />
        <Route path="/document/:filename" element={<DocumentPage />} />
      </Routes>
    </BrowserRouter>
  )
}

export default App

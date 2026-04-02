import { useLocation, useNavigate } from "react-router-dom";
import type { SearchResult } from "./types";

export default function DocumentPage() {
  const location = useLocation();
  const navigate = useNavigate();

  // Retrieving the document data we passed through memory
  const doc = location.state?.doc as SearchResult;

  if (!doc) {
    return (
      <div className="min-h-screen bg-gray-950 flex flex-col items-center justify-center text-white">
        <h1 className="text-2xl font-bold mb-4">Document not found</h1>
        <button onClick={() => navigate('/')} className="text-blue-400 hover:underline">
          Return to Search
        </button>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-950 text-white font-sans p-8 pb-24">
      <div className="max-w-4xl mx-auto mt-8">
        
        {/* Back Button */}
        <button 
          onClick={() => navigate(-1)} 
          className="text-gray-400 hover:text-white flex items-center gap-2 mb-8 transition-colors"
        >
          <span>←</span> Back to Results
        </button>

        {/* Document Header */}
        <div className="border-b border-gray-800 pb-8 mb-8">
          <div className="flex items-center gap-4 mb-4">
            <span className="text-blue-400 bg-blue-900/30 px-3 py-1 rounded-full text-sm font-medium">
              {doc.category}
            </span>
            <span className="text-gray-500 font-mono text-sm">
              File ID: {doc.filename}
            </span>
          </div>
          <h1 className="text-3xl font-bold tracking-tight text-gray-100">
            Document
          </h1>
        </div>

        {/* Full Document Text */}
        <div className="bg-gray-900/50 border border-gray-800 rounded-2xl p-8 sm:p-12 shadow-2xl">
          <p className="text-gray-300 text-lg leading-loose whitespace-pre-wrap font-serif">
            {doc.text}
          </p>
        </div>

      </div>
    </div>
  );
}
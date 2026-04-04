import { useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import type { SearchResult } from "./types";
import { useEffect } from "react";
import { useQuery } from "@tanstack/react-query";

export default function DocumentPage() {
  const { filename } = useParams();
  const navigate = useNavigate();

  const [categories, setCategories] = useState<String[]>([]);
  const [isCatLoading, setIsCatLoading] = useState(true);

  const { data: doc, isLoading: isDocLoading } = useQuery({
    queryKey: ['document', filename],
    queryFn: async () => {
      const res = await fetch(`http://localhost:8000/document/${filename}`);
      if (!res.ok) throw new Error("Failed to fetch document");
      return res.json() as Promise<SearchResult>
    },
    enabled: !!filename, // Only run if filename exists in the URL
  });

  useEffect(() => {
    if (!doc) return;

    const fetchCategories = async () => {
      try {
        const res = await fetch('http://localhost:8000/categories', {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({doc: String(doc.filename)})
        });

        if (!res.ok) {
           throw new Error(`HTTP error! status: ${res.status}`);
        }

        const data = await res.json();
        setCategories(data);
      } catch (error) {
        console.error("Failed to fetch categories", error);
      } finally {
        setIsCatLoading(false);
      }
    };

    fetchCategories();
  }, [doc]);

  if (isDocLoading) {
    return (
      <div className="min-h-screen bg-gray-950 flex flex-col items-center justify-center text-white">
        <div className="w-8 h-8 border-4 border-blue-500 border-t-transparent rounded-full animate-spin mb-4"></div>
        <p className="text-gray-400 font-mono">Retrieving from archives...</p>
      </div>
    );
  }

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

          {/* Dynamic Categories UI */}
          <div className="flex items-center gap-3 flex-wrap">
            <span className="text-sm text-gray-500 font-medium uppercase tracking-wider mr-2">
              Associated Categories:
            </span>
            {isCatLoading ? (
              <span className="text-gray-600 text-sm animate-pulse">Loading data...</span>
            ) : categories.length > 0 ? (
              categories.map((cat, index) => (
                <span key={index} className="border border-gray-700 text-gray-300 px-3 py-1 rounded-full text-xs font-mono bg-gray-900/50">
                  {cat}
                </span>
              ))
            ) : (
              <span className="text-gray-600 text-sm font-mono">None found</span>
            )}
          </div>
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
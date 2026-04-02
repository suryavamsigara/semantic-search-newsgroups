import { useState } from "react";
import { useQuery } from '@tanstack/react-query';
import type { SearchResult } from "./types";

export default function SearchPage() {
  const [query, setQuery] = useState('');
  const [activeCategory, setActiveCategory] = useState<string | null>(null);

  const { data, isLoading } = useQuery({
    queryKey: ['search', query],
    queryFn: async () => {
      if (!query) return null;

      const res = await fetch('http://localhost:8000/search', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({query})
      });
      return res.json() as Promise<SearchResult[]>
    },
    enabled: !!query,
  });

  const results = data || [];
  const topResult = results[0];

  // Filter the remaining results if a category is selected
  const otherResults = results.slice(1).filter(res => 
    activeCategory ? res.category === activeCategory : true
  );

  // Extract unique categories for the filter row
  const categories = Array.from(new Set(results.slice(1).map(r => r.category)));

  return (
    <div className="min-h-screen bg-gray-950 text-white p-8 font-sans">
      
      {/* Search Bar - Center or Top depending on state */}
      <div className={`transition-all duration-500 max-w-2xl mx-auto ${topResult ? 'mb-12' : 'mt-48'}`}>
        <input 
          type="text" 
          className="w-full bg-gray-900 border border-gray-800 rounded-xl px-6 py-4 text-lg focus:ring-2 focus:ring-blue-500 outline-none shadow-2xl"
          placeholder="Search the 20 newsgroups dataset..."
          onKeyDown={(e) => {
            if (e.key === 'Enter') setQuery(e.currentTarget.value);
          }}
        />
      </div>

      {isLoading && <p className="text-center text-gray-500">Searching the archives...</p>}

      {/* The Top Hit */}
      {topResult && (
        <div className="max-w-3xl mx-auto animate-fade-in-up">
          <p className="text-sm text-gray-500 mb-2 uppercase tracking-widest font-semibold">Top Match</p>
          <div className="bg-gray-900 border border-gray-800 rounded-2xl p-8 shadow-2xl relative overflow-hidden">
             {/* Subtle gradient glow effect */}
             <div className="absolute top-0 right-0 w-32 h-32 bg-blue-500/10 rounded-full blur-3xl"></div>
             
             <div className="flex justify-between items-center mb-6">
                <span className="bg-blue-500/20 text-blue-400 px-3 py-1 rounded-full text-sm font-medium">
                  {topResult.category}
                </span>
                <span className="text-green-400 text-sm font-mono bg-green-400/10 px-2 py-1 rounded">
                  {(topResult.score * 100).toFixed(1)}% Confidence
                </span>
             </div>
             
             <p className="text-gray-300 leading-relaxed text-lg line-clamp-4">
               {topResult.text}
             </p>
             
             <button className="mt-6 text-blue-400 hover:text-blue-300 font-medium transition-colors">
               Read Full Document →
             </button>
          </div>
        </div>
      )}

      {/* The "Explore More" Section */}
      {results.length > 1 && (
        <div className="max-w-3xl mx-auto mt-16 border-t border-gray-800 pt-8 animate-fade-in">
          
          <div className="flex items-center justify-between mb-6">
            <h3 className="text-gray-400 font-medium">More Results</h3>
            
            {/* Horizontal Filter Row */}
            <div className="flex gap-2">
              <button 
                onClick={() => setActiveCategory(null)}
                className={`px-3 py-1 text-sm rounded-full ${!activeCategory ? 'bg-white text-black' : 'bg-gray-800 text-gray-400 hover:bg-gray-700'}`}
              >
                All
              </button>
              {categories.map(cat => (
                <button 
                  key={cat}
                  onClick={() => setActiveCategory(cat)}
                  className={`px-3 py-1 text-sm rounded-full ${activeCategory === cat ? 'bg-white text-black' : 'bg-gray-800 text-gray-400 hover:bg-gray-700'}`}
                >
                  {cat}
                </button>
              ))}
            </div>
          </div>

          {/* List of remaining results */}
          <div className="space-y-4">
            {otherResults.map(res => (
              <div key={res.filename} className="p-4 bg-gray-900/50 border border-gray-800/50 rounded-xl hover:bg-gray-800 transition-colors cursor-pointer flex gap-4">
                 <div className="flex-shrink-0 text-gray-500 font-mono text-sm mt-1">{res.category}</div>
                 <p className="text-gray-400 line-clamp-2 text-sm">{res.text}</p>
              </div>
            ))}
          </div>

        </div>
      )}
    </div>
  );
}
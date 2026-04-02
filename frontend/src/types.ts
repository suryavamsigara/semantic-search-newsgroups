export interface SearchResult {
    rank: number;
    score: number;
    category: string;
    filename: string;
    text: string;
}

export interface SearchResponse {
    results: SearchResult[];
}

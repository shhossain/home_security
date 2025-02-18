const API_URL = 'http://localhost:8000/api';


export async function apiClient(path: string, options: RequestInit = {}): Promise<any> {
    const response = await fetch(`${API_URL}${path}`, {
        headers: {
            'Content-Type': 'application/json',
        },
        ...options,
    });

    if (!response.ok) {
        throw new Error(response.statusText);
    }

    return response;
}
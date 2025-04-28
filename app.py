from flask import Flask, render_template, request, jsonify, url_for
import pandas as pd
import numpy as np
from urllib.parse import quote

app = Flask(__name__)

# Load the dataset
df = pd.read_csv("imdb_top_1000.csv")

# Clean the data
df['Released_Year'] = pd.to_numeric(df['Released_Year'], errors='coerce')
df['IMDB_Rating'] = pd.to_numeric(df['IMDB_Rating'], errors='coerce')
df['Meta_score'] = pd.to_numeric(df['Meta_score'], errors='coerce')
df['No_of_Votes'] = pd.to_numeric(df['No_of_Votes'], errors='coerce')

@app.route('/')
def home():
    # Get unique genres for the filter dropdown
    all_genres = set()
    for genres in df['Genre'].str.split(', '):
        if isinstance(genres, list):  # Check if genres is not None
            all_genres.update(genres)
    genres = sorted(list(all_genres))
    
    # Get unique certificates, handle NaN values
    certificates = df['Certificate'].dropna().unique().tolist()
    certificates = sorted([str(cert) for cert in certificates if pd.notna(cert)])
    
    # Get unique years, handle NaN values and ensure they're numbers
    years = df['Released_Year'].dropna().unique().tolist()
    years = sorted([int(year) for year in years if pd.notna(year) and pd.to_numeric(year, errors='coerce') > 0])
    
    return render_template('index.html', 
                         genres=genres,
                         certificates=certificates,
                         years=years)

@app.route('/search')
def search():
    query = request.args.get('q', '')
    genre = request.args.get('genre', '')
    certificate = request.args.get('certificate', '')
    year = request.args.get('year', '')
    
    # Filter the dataset based on search criteria
    filtered_df = df.copy()
    
    if query:
        filtered_df = filtered_df[filtered_df['Series_Title'].str.contains(query, case=False, na=False) |
                                filtered_df['Director'].str.contains(query, case=False, na=False)]
    
    if genre:
        filtered_df = filtered_df[filtered_df['Genre'].str.contains(genre, case=False, na=False)]
    
    if certificate:
        filtered_df = filtered_df[filtered_df['Certificate'].fillna('').astype(str) == str(certificate)]
    
    if year:
        try:
            year_val = int(year)
            filtered_df = filtered_df[filtered_df['Released_Year'].fillna(0) == year_val]
        except ValueError:
            pass
    
    # Convert to list of dictionaries for JSON response
    # Handle NaN values before converting to dict
    filtered_df = filtered_df.replace({np.nan: None})
    movies = filtered_df.to_dict('records')
    
    # Clean up the data for JSON serialization
    for movie in movies:
        for key, value in movie.items():
            if pd.isna(value):
                movie[key] = None
            elif isinstance(value, float) and value.is_integer():
                movie[key] = int(value)
        # Add URL-safe movie title for detail page link
        movie['url_safe_title'] = quote(movie['Series_Title'])
    
    return jsonify(movies)

@app.route('/movie/<path:title>')
def movie_detail(title):
    # Find the movie by title
    movie_data = df[df['Series_Title'] == title]
    
    if not movie_data.empty:
        movie = movie_data.iloc[0].to_dict()
        # Convert NaN values to empty strings and clean up numbers
        cleaned_movie = {}
        for k, v in movie.items():
            if pd.isna(v):
                cleaned_movie[k] = ''
            elif isinstance(v, float) and v.is_integer():
                cleaned_movie[k] = int(v)
            else:
                cleaned_movie[k] = v
        return render_template('movie_detail.html', movie=cleaned_movie)
    return "Movie not found", 404

if __name__ == '__main__':
    app.run(debug=True) 
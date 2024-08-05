CREATE OR REPLACE DATABASE PdfEmbeddings;

CREATE TABLE IF EXISTS FileItem(
    id INTEGER NOT NULL KEY AUTOINCREMENT,
    title varchar(200) NOT NULL,
    uploaded_date DATETIME NOT NULL,
    file_source TEXT NOT NULL,
    active boolean not null
)
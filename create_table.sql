CREATE TABLE Device_Info(
    MAC TEXT PRIMARY KEY NOT NULL,
    NAME TEXT NOT NULL,
    DESCRIBE TEXT,
    ID INT NOT NULL UNIQUE
);

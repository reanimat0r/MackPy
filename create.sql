CREATE TABLE user(
	`chat_id`	TEXT NOT NULL UNIQUE,
	`tia`	INTEGER NOT NULL UNIQUE,
	`pwd`	TEXT,
	`last_refresh`	TEXT,
    `tarefas_interval` INTEGER,
	PRIMARY KEY(chat_id,tia)
);
CREATE TABLE horario (
	`tia`			INTEGER NOT NULL UNIQUE,
	`json`	TEXT,
	FOREIGN KEY(tia) REFERENCES users(tia)
);
CREATE TABLE materia(
	tia INTEGER PRIMARY KEY,
	json TEXT,
	FOREIGN KEY(tia) REFERENCES users(tia)
);
CREATE TABLE nota(
	tia INTEGER PRIMARY KEY,
    json TEXT,    
	FOREIGN KEY(tia) REFERENCES users(tia)
);

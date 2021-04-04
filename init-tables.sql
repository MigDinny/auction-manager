CREATE TABLE auctions (
	id			 SERIAL,
	article_id		 BIGINT NOT NULL UNIQUE,
	title		 VARCHAR(512) NOT NULL,
	price		 INTEGER NOT NULL,
	end_date		 TIMESTAMP NOT NULL,
	highest_bidder_id	 INTEGER,
	status		 BOOL NOT NULL DEFAULT TRUE,
	last_description_id INTEGER NOT NULL,
	seller_id		 INTEGER NOT NULL,
	PRIMARY KEY(id)
);

CREATE TABLE users (
	id	 SERIAL,
	username VARCHAR(32) NOT NULL UNIQUE,
	password VARCHAR(32) NOT NULL ,
	email	 VARCHAR(64) NOT NULL UNIQUE,
	token	 VARCHAR(32) UNIQUE,
	PRIMARY KEY(id)
);

CREATE TABLE notifications (
	id	 SERIAL,
	text	 VARCHAR(512),
	time_stamp TIMESTAMP NOT NULL,
	users_id	 INTEGER NOT NULL,
	PRIMARY KEY(id)
);

CREATE TABLE messages (
	id		 SERIAL,
	text	 CHAR(255),
	time_stamp	 TIMESTAMP NOT NULL,
	auctions_id INTEGER NOT NULL,
	users_id	 INTEGER NOT NULL,
	PRIMARY KEY(id)
);

CREATE TABLE biddings (
	id		 SERIAL,
	price	 INTEGER NOT NULL,
	time_stamp	 TIMESTAMP NOT NULL,
	auctions_id INTEGER NOT NULL,
	users_id	 INTEGER NOT NULL,
	PRIMARY KEY(id)
);

CREATE TABLE descriptions (
	id		 SERIAL,
	text	 VARCHAR(1024) NOT NULL,
	time_stamp	 TIMESTAMP NOT NULL,
	auctions_id INTEGER NOT NULL,
	PRIMARY KEY(id)
);

ALTER TABLE auctions ADD CONSTRAINT auctions_seller_fk FOREIGN KEY (seller_id) REFERENCES users(id);
ALTER TABLE auctions ADD CONSTRAINT auctions_bidder_fk FOREIGN KEY (highest_bidder_id) REFERENCES users(id);
ALTER TABLE auctions ADD CONSTRAINT auctions_description_fk FOREIGN KEY (last_description_id) REFERENCES descriptions(id);

ALTER TABLE notifications ADD CONSTRAINT notifications_user_fk FOREIGN KEY (users_id) REFERENCES users(id);

ALTER TABLE messages ADD CONSTRAINT messages_auction_fk FOREIGN KEY (auctions_id) REFERENCES auctions(id);
ALTER TABLE messages ADD CONSTRAINT messages_user_fk FOREIGN KEY (users_id) REFERENCES users(id);

ALTER TABLE biddings ADD CONSTRAINT biddings_auction_fk FOREIGN KEY (auctions_id) REFERENCES auctions(id);
ALTER TABLE biddings ADD CONSTRAINT biddings_user_fk FOREIGN KEY (users_id) REFERENCES users(id);

ALTER TABLE descriptions ADD CONSTRAINT descriptions_auction_fk FOREIGN KEY (auctions_id) REFERENCES auctions(id);


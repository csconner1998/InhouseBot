SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;
SET default_tablespace = '';
SET default_table_access_method = heap;

-- Active Matches

CREATE TABLE "public"."active_matches" (
    "active_id" integer NOT NULL,
    "top1" bigint,
    "top2" bigint,
    "jungle1" bigint,
    "jungle2" bigint,
    "mid1" bigint,
    "mid2" bigint,
    "adc1" bigint,
    "adc2" bigint,
    "support1" bigint,
    "support2" bigint,
    "win_msg_id" "text",
    "react_msg_id" "text"
);
ALTER TABLE public.active_matches OWNER TO utahesports;
CREATE SEQUENCE "public"."active_matches_active_id_seq"
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
ALTER TABLE public.active_matches_active_id_seq OWNER TO utahesports;
ALTER SEQUENCE "public"."active_matches_active_id_seq" OWNED BY "public"."active_matches"."active_id";

-- Match Reporters

CREATE TABLE "public"."match_reporters" (
    "player_id" bigint NOT NULL
);
ALTER TABLE public.match_reporters OWNER TO utahesports;

CREATE TABLE "public"."matches" (
    "matchid" integer NOT NULL,
    "created" timestamp without time zone NOT NULL,
    "winner" character varying(50) NOT NULL
);
ALTER TABLE public.matches OWNER TO utahesports;
CREATE SEQUENCE "public"."matches_matchid_seq"
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
ALTER TABLE public.matches_matchid_seq OWNER TO utahesports;
ALTER SEQUENCE "public"."matches_matchid_seq" OWNED BY "public"."matches"."matchid";

-- Match players

CREATE TABLE "public"."matches_players" (
    "match_id" integer NOT NULL,
    "player_id" bigint NOT NULL,
    "blue" boolean NOT NULL,
    "role" integer
);
ALTER TABLE public.matches_players OWNER TO utahesports;
CREATE SEQUENCE "public"."matches_players_match_id_seq"
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
ALTER TABLE public.matches_players_match_id_seq OWNER TO utahesports;
ALTER SEQUENCE "public"."matches_players_match_id_seq" OWNED BY "public"."matches_players"."match_id";
CREATE SEQUENCE "public"."matches_players_player_id_seq"
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
ALTER TABLE public.matches_players_player_id_seq OWNER TO utahesports;
ALTER SEQUENCE "public"."matches_players_player_id_seq" OWNED BY "public"."matches_players"."player_id";

-- PLayers

CREATE TABLE "public"."players" (
    "id" bigint NOT NULL,
    "name" character varying(50) NOT NULL,
    "win" integer NOT NULL,
    "loss" integer NOT NULL,
    "sp" integer NOT NULL,
    "show_rank" boolean
);
ALTER TABLE public.players OWNER TO utahesports;
CREATE SEQUENCE "public"."players_id_seq"
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
ALTER TABLE public.players_id_seq OWNER TO utahesports;
ALTER SEQUENCE "public"."players_id_seq" OWNED BY "public"."players"."id";

-- Roles

CREATE TABLE "public"."roles" (
    "roleid" integer NOT NULL,
    "role" "text" NOT NULL
);
ALTER TABLE public.roles OWNER TO utahesports;
CREATE SEQUENCE "public"."roles_roleid_seq"
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;
ALTER TABLE public.roles_roleid_seq OWNER TO utahesports;
ALTER SEQUENCE "public"."roles_roleid_seq" OWNED BY "public"."roles"."roleid";

-- Coins

CREATE TABLE "public"."coins" (
    "discord_id" bigint NOT NULL,
    "coin_count" integer NOT NULL
);
ALTER TABLE public.roles OWNER TO utahesports;

CREATE TABLE "public"."soloqueue_leaderboard" (
    "discord_id" bigint NOT NULL,
    "league_name" "text" NOT NULL
);
ALTER TABLE public.roles OWNER TO utahesports;

-- Sequence ID setip

ALTER TABLE ONLY "public"."active_matches" ALTER COLUMN "active_id" SET DEFAULT "nextval"('"public"."active_matches_active_id_seq"'::"regclass");
ALTER TABLE ONLY "public"."matches" ALTER COLUMN "matchid" SET DEFAULT "nextval"('"public"."matches_matchid_seq"'::"regclass");
ALTER TABLE ONLY "public"."matches_players" ALTER COLUMN "match_id" SET DEFAULT "nextval"('"public"."matches_players_match_id_seq"'::"regclass");
ALTER TABLE ONLY "public"."matches_players" ALTER COLUMN "player_id" SET DEFAULT "nextval"('"public"."matches_players_player_id_seq"'::"regclass");
ALTER TABLE ONLY "public"."players" ALTER COLUMN "id" SET DEFAULT "nextval"('"public"."players_id_seq"'::"regclass");
ALTER TABLE ONLY "public"."roles" ALTER COLUMN "roleid" SET DEFAULT "nextval"('"public"."roles_roleid_seq"'::"regclass");

-- Insert static role data

COPY "public"."roles" ("roleid", "role") FROM stdin;
0	top
1	jungle
2	middle
3	adc
4	support
\.

-- PKs

ALTER TABLE ONLY "public"."active_matches"
    ADD CONSTRAINT "active_matches_pkey" PRIMARY KEY ("active_id");

ALTER TABLE ONLY "public"."match_reporters"
    ADD CONSTRAINT "match_reporters_pkey" PRIMARY KEY ("player_id");

ALTER TABLE ONLY "public"."matches"
    ADD CONSTRAINT "matches_pkey" PRIMARY KEY ("matchid");

ALTER TABLE ONLY "public"."matches_players"
    ADD CONSTRAINT "matches_players_pkey" PRIMARY KEY ("match_id", "player_id");

ALTER TABLE ONLY "public"."players"
    ADD CONSTRAINT "players_name_key" UNIQUE ("name");

ALTER TABLE ONLY "public"."players"
    ADD CONSTRAINT "players_pkey" PRIMARY KEY ("id");

ALTER TABLE ONLY "public"."roles"
    ADD CONSTRAINT "roles_pkey" PRIMARY KEY ("roleid");

ALTER TABLE ONLY "public"."coins"
    ADD CONSTRAINT "coins_pkey" PRIMARY KEY ("discord_id");

-- FKs

ALTER TABLE ONLY "public"."active_matches"
    ADD CONSTRAINT "fk_adc1" FOREIGN KEY ("adc1") REFERENCES "public"."players"("id");

ALTER TABLE ONLY "public"."active_matches"
    ADD CONSTRAINT "fk_adc2" FOREIGN KEY ("adc2") REFERENCES "public"."players"("id");

ALTER TABLE ONLY "public"."active_matches"
    ADD CONSTRAINT "fk_jungle1" FOREIGN KEY ("jungle1") REFERENCES "public"."players"("id");

ALTER TABLE ONLY "public"."active_matches"
    ADD CONSTRAINT "fk_jungle2" FOREIGN KEY ("jungle2") REFERENCES "public"."players"("id");

ALTER TABLE ONLY "public"."matches_players"
    ADD CONSTRAINT "fk_match_id" FOREIGN KEY ("match_id") REFERENCES "public"."matches"("matchid");

ALTER TABLE ONLY "public"."active_matches"
    ADD CONSTRAINT "fk_mid1" FOREIGN KEY ("mid1") REFERENCES "public"."players"("id");

ALTER TABLE ONLY "public"."active_matches"
    ADD CONSTRAINT "fk_mid2" FOREIGN KEY ("mid2") REFERENCES "public"."players"("id");

ALTER TABLE ONLY "public"."matches_players"
    ADD CONSTRAINT "fk_player_id" FOREIGN KEY ("player_id") REFERENCES "public"."players"("id");

ALTER TABLE ONLY "public"."matches_players"
    ADD CONSTRAINT "fk_role" FOREIGN KEY ("role") REFERENCES "public"."roles"("roleid");

ALTER TABLE ONLY "public"."active_matches"
    ADD CONSTRAINT "fk_support1" FOREIGN KEY ("support1") REFERENCES "public"."players"("id");

ALTER TABLE ONLY "public"."active_matches"
    ADD CONSTRAINT "fk_support2" FOREIGN KEY ("support2") REFERENCES "public"."players"("id");

ALTER TABLE ONLY "public"."active_matches"
    ADD CONSTRAINT "fk_top1" FOREIGN KEY ("top1") REFERENCES "public"."players"("id");

ALTER TABLE ONLY "public"."active_matches"
    ADD CONSTRAINT "fk_top2" FOREIGN KEY ("top2") REFERENCES "public"."players"("id");
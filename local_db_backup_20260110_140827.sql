--
-- PostgreSQL database dump
--

\restrict wQ6RXHF6LkfSu0cKdYRMiXZZMSZZxmI5NPUugAiQV3UQkbfC2XjULspUjQjkoke

-- Dumped from database version 14.20 (Homebrew)
-- Dumped by pg_dump version 14.20 (Homebrew)

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

--
-- Name: feature_snapshots; Type: TABLE; Schema: public; Owner: iabadvisors
--

CREATE TABLE public.feature_snapshots (
    id integer NOT NULL,
    market_id character varying(66) NOT NULL,
    snapshot_time timestamp without time zone NOT NULL,
    features jsonb NOT NULL,
    embeddings_path character varying(255),
    created_at timestamp without time zone DEFAULT now()
);


ALTER TABLE public.feature_snapshots OWNER TO iabadvisors;

--
-- Name: feature_snapshots_id_seq; Type: SEQUENCE; Schema: public; Owner: iabadvisors
--

CREATE SEQUENCE public.feature_snapshots_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.feature_snapshots_id_seq OWNER TO iabadvisors;

--
-- Name: feature_snapshots_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: iabadvisors
--

ALTER SEQUENCE public.feature_snapshots_id_seq OWNED BY public.feature_snapshots.id;


--
-- Name: markets; Type: TABLE; Schema: public; Owner: iabadvisors
--

CREATE TABLE public.markets (
    id integer NOT NULL,
    market_id character varying(66) NOT NULL,
    condition_id character varying(66) NOT NULL,
    question text NOT NULL,
    category character varying(50),
    resolution_date timestamp without time zone,
    outcome character varying(3),
    created_at timestamp without time zone DEFAULT now(),
    resolved_at timestamp without time zone
);


ALTER TABLE public.markets OWNER TO iabadvisors;

--
-- Name: markets_id_seq; Type: SEQUENCE; Schema: public; Owner: iabadvisors
--

CREATE SEQUENCE public.markets_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.markets_id_seq OWNER TO iabadvisors;

--
-- Name: markets_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: iabadvisors
--

ALTER SEQUENCE public.markets_id_seq OWNED BY public.markets.id;


--
-- Name: model_performance; Type: TABLE; Schema: public; Owner: iabadvisors
--

CREATE TABLE public.model_performance (
    id integer NOT NULL,
    model_name character varying(50) NOT NULL,
    model_version character varying(50) NOT NULL,
    evaluation_date date NOT NULL,
    accuracy numeric(10,6),
    brier_score numeric(10,6),
    log_loss numeric(10,6),
    auc_roc numeric(10,6),
    sample_count integer,
    created_at timestamp without time zone DEFAULT now()
);


ALTER TABLE public.model_performance OWNER TO iabadvisors;

--
-- Name: model_performance_id_seq; Type: SEQUENCE; Schema: public; Owner: iabadvisors
--

CREATE SEQUENCE public.model_performance_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.model_performance_id_seq OWNER TO iabadvisors;

--
-- Name: model_performance_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: iabadvisors
--

ALTER SEQUENCE public.model_performance_id_seq OWNED BY public.model_performance.id;


--
-- Name: portfolio_snapshots; Type: TABLE; Schema: public; Owner: iabadvisors
--

CREATE TABLE public.portfolio_snapshots (
    id integer NOT NULL,
    snapshot_time timestamp without time zone NOT NULL,
    total_value numeric(20,8) NOT NULL,
    cash numeric(20,8) NOT NULL,
    positions_value numeric(20,8) NOT NULL,
    total_exposure numeric(20,8) NOT NULL,
    daily_pnl numeric(20,8),
    unrealized_pnl numeric(20,8),
    realized_pnl numeric(20,8),
    created_at timestamp without time zone DEFAULT now()
);


ALTER TABLE public.portfolio_snapshots OWNER TO iabadvisors;

--
-- Name: portfolio_snapshots_id_seq; Type: SEQUENCE; Schema: public; Owner: iabadvisors
--

CREATE SEQUENCE public.portfolio_snapshots_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.portfolio_snapshots_id_seq OWNER TO iabadvisors;

--
-- Name: portfolio_snapshots_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: iabadvisors
--

ALTER SEQUENCE public.portfolio_snapshots_id_seq OWNED BY public.portfolio_snapshots.id;


--
-- Name: predictions; Type: TABLE; Schema: public; Owner: iabadvisors
--

CREATE TABLE public.predictions (
    id integer NOT NULL,
    market_id character varying(66) NOT NULL,
    prediction_time timestamp without time zone NOT NULL,
    model_probability numeric(10,6) NOT NULL,
    market_price numeric(10,6) NOT NULL,
    edge numeric(10,6) NOT NULL,
    confidence numeric(10,6) NOT NULL,
    model_version character varying(50) NOT NULL,
    model_predictions jsonb,
    created_at timestamp without time zone DEFAULT now()
);


ALTER TABLE public.predictions OWNER TO iabadvisors;

--
-- Name: predictions_id_seq; Type: SEQUENCE; Schema: public; Owner: iabadvisors
--

CREATE SEQUENCE public.predictions_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.predictions_id_seq OWNER TO iabadvisors;

--
-- Name: predictions_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: iabadvisors
--

ALTER SEQUENCE public.predictions_id_seq OWNED BY public.predictions.id;


--
-- Name: signals; Type: TABLE; Schema: public; Owner: iabadvisors
--

CREATE TABLE public.signals (
    id integer NOT NULL,
    prediction_id integer,
    market_id character varying(66) NOT NULL,
    side character varying(3) NOT NULL,
    signal_strength character varying(10) NOT NULL,
    suggested_size numeric(20,8),
    executed boolean DEFAULT false,
    created_at timestamp without time zone DEFAULT now()
);


ALTER TABLE public.signals OWNER TO iabadvisors;

--
-- Name: signals_id_seq; Type: SEQUENCE; Schema: public; Owner: iabadvisors
--

CREATE SEQUENCE public.signals_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.signals_id_seq OWNER TO iabadvisors;

--
-- Name: signals_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: iabadvisors
--

ALTER SEQUENCE public.signals_id_seq OWNED BY public.signals.id;


--
-- Name: trades; Type: TABLE; Schema: public; Owner: iabadvisors
--

CREATE TABLE public.trades (
    id integer NOT NULL,
    signal_id integer,
    market_id character varying(66) NOT NULL,
    side character varying(3) NOT NULL,
    entry_price numeric(10,6) NOT NULL,
    size numeric(20,8) NOT NULL,
    exit_price numeric(10,6),
    pnl numeric(20,8),
    status character varying(20) NOT NULL,
    entry_time timestamp without time zone NOT NULL,
    exit_time timestamp without time zone,
    created_at timestamp without time zone DEFAULT now()
);


ALTER TABLE public.trades OWNER TO iabadvisors;

--
-- Name: trades_id_seq; Type: SEQUENCE; Schema: public; Owner: iabadvisors
--

CREATE SEQUENCE public.trades_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.trades_id_seq OWNER TO iabadvisors;

--
-- Name: trades_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: iabadvisors
--

ALTER SEQUENCE public.trades_id_seq OWNED BY public.trades.id;


--
-- Name: feature_snapshots id; Type: DEFAULT; Schema: public; Owner: iabadvisors
--

ALTER TABLE ONLY public.feature_snapshots ALTER COLUMN id SET DEFAULT nextval('public.feature_snapshots_id_seq'::regclass);


--
-- Name: markets id; Type: DEFAULT; Schema: public; Owner: iabadvisors
--

ALTER TABLE ONLY public.markets ALTER COLUMN id SET DEFAULT nextval('public.markets_id_seq'::regclass);


--
-- Name: model_performance id; Type: DEFAULT; Schema: public; Owner: iabadvisors
--

ALTER TABLE ONLY public.model_performance ALTER COLUMN id SET DEFAULT nextval('public.model_performance_id_seq'::regclass);


--
-- Name: portfolio_snapshots id; Type: DEFAULT; Schema: public; Owner: iabadvisors
--

ALTER TABLE ONLY public.portfolio_snapshots ALTER COLUMN id SET DEFAULT nextval('public.portfolio_snapshots_id_seq'::regclass);


--
-- Name: predictions id; Type: DEFAULT; Schema: public; Owner: iabadvisors
--

ALTER TABLE ONLY public.predictions ALTER COLUMN id SET DEFAULT nextval('public.predictions_id_seq'::regclass);


--
-- Name: signals id; Type: DEFAULT; Schema: public; Owner: iabadvisors
--

ALTER TABLE ONLY public.signals ALTER COLUMN id SET DEFAULT nextval('public.signals_id_seq'::regclass);


--
-- Name: trades id; Type: DEFAULT; Schema: public; Owner: iabadvisors
--

ALTER TABLE ONLY public.trades ALTER COLUMN id SET DEFAULT nextval('public.trades_id_seq'::regclass);


--
-- Data for Name: feature_snapshots; Type: TABLE DATA; Schema: public; Owner: iabadvisors
--

COPY public.feature_snapshots (id, market_id, snapshot_time, features, embeddings_path, created_at) FROM stdin;
\.


--
-- Data for Name: markets; Type: TABLE DATA; Schema: public; Owner: iabadvisors
--

COPY public.markets (id, market_id, condition_id, question, category, resolution_date, outcome, created_at, resolved_at) FROM stdin;
1	0x7c97080dfbbe71bfa52ba51c82cb0cdfe47cd7b87842047c58647c8ff1d1fef4	0x7c97080dfbbe71bfa52ba51c82cb0cdfe47cd7b87842047c58647c8ff1d1fef4	Will the FDV of OpenSea's token 1 week after launch be above Blur's FDV?	\N	2023-12-30 00:00:00	\N	2026-01-09 09:28:37.547815	\N
2	0x3784ea734e3886a167bf3d8de6b79290e2dcf57e71812f9db5cfe165936d3215	0x3784ea734e3886a167bf3d8de6b79290e2dcf57e71812f9db5cfe165936d3215	Will the FDV of OpenSea's token be above $5b 1 week after launch?	\N	2023-12-30 00:00:00	\N	2026-01-09 09:29:07.459967	\N
3	0x7ce4ccf36719db44a83d2f124249099cfd74f248ce9a1ca00c4e8cab278c1b1f	0x7ce4ccf36719db44a83d2f124249099cfd74f248ce9a1ca00c4e8cab278c1b1f	Will the FDV of OpenSea's token be above $15b 1 week after launch?	\N	2023-12-30 00:00:00	\N	2026-01-09 09:29:08.151851	\N
4	0x34cf158202fa1b5ef7353355c78abead09788c12d0dd3e48d1809429b91f0405	0x34cf158202fa1b5ef7353355c78abead09788c12d0dd3e48d1809429b91f0405	Will GPT-4 have 500b+ parameters?	\N	2023-12-31 00:00:00	\N	2026-01-09 09:43:10.496896	\N
5	0x79ca3466ee91a3c956d317a3bef4497df2bf6c972f199346586dd9b2f7c4d996	0x79ca3466ee91a3c956d317a3bef4497df2bf6c972f199346586dd9b2f7c4d996	Will the FDV of OpenSea's token be above $10b 1 week after launch?	\N	2023-12-30 00:00:00	\N	2026-01-09 09:43:11.206199	\N
\.


--
-- Data for Name: model_performance; Type: TABLE DATA; Schema: public; Owner: iabadvisors
--

COPY public.model_performance (id, model_name, model_version, evaluation_date, accuracy, brier_score, log_loss, auc_roc, sample_count, created_at) FROM stdin;
\.


--
-- Data for Name: portfolio_snapshots; Type: TABLE DATA; Schema: public; Owner: iabadvisors
--

COPY public.portfolio_snapshots (id, snapshot_time, total_value, cash, positions_value, total_exposure, daily_pnl, unrealized_pnl, realized_pnl, created_at) FROM stdin;
1	2026-01-09 15:50:43.520556	10000.00000000	9500.00000000	500.00000000	500.00000000	25.30000000	125.50000000	0.00000000	2026-01-09 09:50:43.519315
\.


--
-- Data for Name: predictions; Type: TABLE DATA; Schema: public; Owner: iabadvisors
--

COPY public.predictions (id, market_id, prediction_time, model_probability, market_price, edge, confidence, model_version, model_predictions, created_at) FROM stdin;
1	0x7c97080dfbbe71bfa52ba51c82cb0cdfe47cd7b87842047c58647c8ff1d1fef4	2026-01-09 15:29:07.450377	0.779203	0.500000	0.279203	0.463637	v1.0	{"xgboost": 0.978634238243103, "lightgbm": 0.978634238243103}	2026-01-09 09:29:06.749172
2	0x3784ea734e3886a167bf3d8de6b79290e2dcf57e71812f9db5cfe165936d3215	2026-01-09 15:29:08.148246	0.779203	0.500000	0.279203	0.463637	v1.0	{"xgboost": 0.978634238243103, "lightgbm": 0.978634238243103}	2026-01-09 09:29:07.46322
3	0x7ce4ccf36719db44a83d2f124249099cfd74f248ce9a1ca00c4e8cab278c1b1f	2026-01-09 15:29:08.85533	0.779203	0.500000	0.279203	0.463637	v1.0	{"xgboost": 0.978634238243103, "lightgbm": 0.978634238243103}	2026-01-09 09:29:08.154069
4	0x7c97080dfbbe71bfa52ba51c82cb0cdfe47cd7b87842047c58647c8ff1d1fef4	2026-01-09 15:43:09.158228	0.779203	0.500000	0.279203	0.463637	v1.0	{"xgboost": 0.978634238243103, "lightgbm": 0.978634238243103}	2026-01-09 09:43:08.362147
5	0x3784ea734e3886a167bf3d8de6b79290e2dcf57e71812f9db5cfe165936d3215	2026-01-09 15:43:09.846892	0.779203	0.500000	0.279203	0.463637	v1.0	{"xgboost": 0.978634238243103, "lightgbm": 0.978634238243103}	2026-01-09 09:43:09.165163
6	0x7ce4ccf36719db44a83d2f124249099cfd74f248ce9a1ca00c4e8cab278c1b1f	2026-01-09 15:43:10.492462	0.779203	0.500000	0.279203	0.463637	v1.0	{"xgboost": 0.978634238243103, "lightgbm": 0.978634238243103}	2026-01-09 09:43:09.849673
7	0x34cf158202fa1b5ef7353355c78abead09788c12d0dd3e48d1809429b91f0405	2026-01-09 15:43:11.202857	0.779203	0.500000	0.279203	0.463637	v1.0	{"xgboost": 0.978634238243103, "lightgbm": 0.978634238243103}	2026-01-09 09:43:10.500992
8	0x79ca3466ee91a3c956d317a3bef4497df2bf6c972f199346586dd9b2f7c4d996	2026-01-09 15:43:11.845251	0.779203	0.500000	0.279203	0.463637	v1.0	{"xgboost": 0.978634238243103, "lightgbm": 0.978634238243103}	2026-01-09 09:43:11.2086
9	0x7c97080dfbbe71bfa52ba51c82cb0cdfe47cd7b87842047c58647c8ff1d1fef4	2026-01-09 15:45:59.23254	0.875455	0.500000	0.375455	0.673349	v1.0	{"xgboost": 0.978634238243103, "lightgbm": 0.7310040402999396}	2026-01-09 09:45:58.448625
10	0x3784ea734e3886a167bf3d8de6b79290e2dcf57e71812f9db5cfe165936d3215	2026-01-09 15:45:59.913529	0.875455	0.500000	0.375455	0.673349	v1.0	{"xgboost": 0.978634238243103, "lightgbm": 0.7310040402999396}	2026-01-09 09:45:59.238895
11	0x7ce4ccf36719db44a83d2f124249099cfd74f248ce9a1ca00c4e8cab278c1b1f	2026-01-09 15:46:00.625204	0.875455	0.500000	0.375455	0.673349	v1.0	{"xgboost": 0.978634238243103, "lightgbm": 0.7310040402999396}	2026-01-09 09:45:59.916235
12	0x34cf158202fa1b5ef7353355c78abead09788c12d0dd3e48d1809429b91f0405	2026-01-09 15:46:01.398987	0.875455	0.500000	0.375455	0.673349	v1.0	{"xgboost": 0.978634238243103, "lightgbm": 0.7310040402999396}	2026-01-09 09:46:00.63015
13	0x79ca3466ee91a3c956d317a3bef4497df2bf6c972f199346586dd9b2f7c4d996	2026-01-09 15:46:02.230911	0.875455	0.500000	0.375455	0.673349	v1.0	{"xgboost": 0.978634238243103, "lightgbm": 0.7310040402999396}	2026-01-09 09:46:01.401871
\.


--
-- Data for Name: signals; Type: TABLE DATA; Schema: public; Owner: iabadvisors
--

COPY public.signals (id, prediction_id, market_id, side, signal_strength, suggested_size, executed, created_at) FROM stdin;
1	9	0x7c97080dfbbe71bfa52ba51c82cb0cdfe47cd7b87842047c58647c8ff1d1fef4	YES	STRONG	100.00000000	f	2026-01-09 09:50:09.032826
2	10	0x3784ea734e3886a167bf3d8de6b79290e2dcf57e71812f9db5cfe165936d3215	YES	STRONG	100.00000000	f	2026-01-09 09:50:09.032826
3	11	0x7ce4ccf36719db44a83d2f124249099cfd74f248ce9a1ca00c4e8cab278c1b1f	YES	STRONG	100.00000000	f	2026-01-09 09:50:09.032826
4	12	0x34cf158202fa1b5ef7353355c78abead09788c12d0dd3e48d1809429b91f0405	YES	STRONG	100.00000000	f	2026-01-09 09:50:09.032826
5	13	0x79ca3466ee91a3c956d317a3bef4497df2bf6c972f199346586dd9b2f7c4d996	YES	STRONG	100.00000000	f	2026-01-09 09:50:09.032826
6	6	0x7ce4ccf36719db44a83d2f124249099cfd74f248ce9a1ca00c4e8cab278c1b1f	YES	STRONG	100.00000000	f	2026-01-09 09:50:09.032826
7	1	0x7c97080dfbbe71bfa52ba51c82cb0cdfe47cd7b87842047c58647c8ff1d1fef4	YES	STRONG	100.00000000	f	2026-01-09 09:50:09.032826
8	8	0x79ca3466ee91a3c956d317a3bef4497df2bf6c972f199346586dd9b2f7c4d996	YES	STRONG	100.00000000	f	2026-01-09 09:50:09.032826
9	7	0x34cf158202fa1b5ef7353355c78abead09788c12d0dd3e48d1809429b91f0405	YES	STRONG	100.00000000	f	2026-01-09 09:50:09.032826
10	2	0x3784ea734e3886a167bf3d8de6b79290e2dcf57e71812f9db5cfe165936d3215	YES	STRONG	100.00000000	f	2026-01-09 09:50:09.032826
11	3	0x7ce4ccf36719db44a83d2f124249099cfd74f248ce9a1ca00c4e8cab278c1b1f	YES	STRONG	100.00000000	f	2026-01-09 09:50:23.487187
12	4	0x7c97080dfbbe71bfa52ba51c82cb0cdfe47cd7b87842047c58647c8ff1d1fef4	YES	STRONG	100.00000000	f	2026-01-09 09:50:23.487187
13	5	0x3784ea734e3886a167bf3d8de6b79290e2dcf57e71812f9db5cfe165936d3215	YES	STRONG	100.00000000	f	2026-01-09 09:50:23.487187
\.


--
-- Data for Name: trades; Type: TABLE DATA; Schema: public; Owner: iabadvisors
--

COPY public.trades (id, signal_id, market_id, side, entry_price, size, exit_price, pnl, status, entry_time, exit_time, created_at) FROM stdin;
1	1	0x7c97080dfbbe71bfa52ba51c82cb0cdfe47cd7b87842047c58647c8ff1d1fef4	YES	0.500000	100.00000000	\N	\N	OPEN	2026-01-09 15:50:09.046441	\N	2026-01-09 09:50:09.04434
2	2	0x3784ea734e3886a167bf3d8de6b79290e2dcf57e71812f9db5cfe165936d3215	YES	0.500000	100.00000000	\N	\N	OPEN	2026-01-09 15:50:09.046479	\N	2026-01-09 09:50:09.04434
3	3	0x7ce4ccf36719db44a83d2f124249099cfd74f248ce9a1ca00c4e8cab278c1b1f	YES	0.500000	100.00000000	\N	\N	OPEN	2026-01-09 15:50:09.046494	\N	2026-01-09 09:50:09.04434
4	4	0x34cf158202fa1b5ef7353355c78abead09788c12d0dd3e48d1809429b91f0405	YES	0.500000	100.00000000	\N	\N	OPEN	2026-01-09 15:50:09.046505	\N	2026-01-09 09:50:09.04434
5	5	0x79ca3466ee91a3c956d317a3bef4497df2bf6c972f199346586dd9b2f7c4d996	YES	0.500000	100.00000000	\N	\N	OPEN	2026-01-09 15:50:09.046516	\N	2026-01-09 09:50:09.04434
6	6	0x7ce4ccf36719db44a83d2f124249099cfd74f248ce9a1ca00c4e8cab278c1b1f	YES	0.500000	100.00000000	\N	\N	OPEN	2026-01-09 15:50:23.499531	\N	2026-01-09 09:50:23.496796
7	7	0x7c97080dfbbe71bfa52ba51c82cb0cdfe47cd7b87842047c58647c8ff1d1fef4	YES	0.500000	100.00000000	\N	\N	OPEN	2026-01-09 15:50:23.499571	\N	2026-01-09 09:50:23.496796
8	8	0x79ca3466ee91a3c956d317a3bef4497df2bf6c972f199346586dd9b2f7c4d996	YES	0.500000	100.00000000	\N	\N	OPEN	2026-01-09 15:50:23.499587	\N	2026-01-09 09:50:23.496796
9	9	0x34cf158202fa1b5ef7353355c78abead09788c12d0dd3e48d1809429b91f0405	YES	0.500000	100.00000000	\N	\N	OPEN	2026-01-09 15:50:23.499599	\N	2026-01-09 09:50:23.496796
10	10	0x3784ea734e3886a167bf3d8de6b79290e2dcf57e71812f9db5cfe165936d3215	YES	0.500000	100.00000000	\N	\N	OPEN	2026-01-09 15:50:23.49961	\N	2026-01-09 09:50:23.496796
11	11	0x7ce4ccf36719db44a83d2f124249099cfd74f248ce9a1ca00c4e8cab278c1b1f	YES	0.500000	100.00000000	\N	\N	OPEN	2026-01-09 15:50:43.514223	\N	2026-01-09 09:50:43.51242
12	12	0x7c97080dfbbe71bfa52ba51c82cb0cdfe47cd7b87842047c58647c8ff1d1fef4	YES	0.500000	100.00000000	\N	\N	OPEN	2026-01-09 15:50:43.514271	\N	2026-01-09 09:50:43.51242
13	13	0x3784ea734e3886a167bf3d8de6b79290e2dcf57e71812f9db5cfe165936d3215	YES	0.500000	100.00000000	\N	\N	OPEN	2026-01-09 15:50:43.51429	\N	2026-01-09 09:50:43.51242
\.


--
-- Name: feature_snapshots_id_seq; Type: SEQUENCE SET; Schema: public; Owner: iabadvisors
--

SELECT pg_catalog.setval('public.feature_snapshots_id_seq', 1, false);


--
-- Name: markets_id_seq; Type: SEQUENCE SET; Schema: public; Owner: iabadvisors
--

SELECT pg_catalog.setval('public.markets_id_seq', 5, true);


--
-- Name: model_performance_id_seq; Type: SEQUENCE SET; Schema: public; Owner: iabadvisors
--

SELECT pg_catalog.setval('public.model_performance_id_seq', 1, false);


--
-- Name: portfolio_snapshots_id_seq; Type: SEQUENCE SET; Schema: public; Owner: iabadvisors
--

SELECT pg_catalog.setval('public.portfolio_snapshots_id_seq', 1, true);


--
-- Name: predictions_id_seq; Type: SEQUENCE SET; Schema: public; Owner: iabadvisors
--

SELECT pg_catalog.setval('public.predictions_id_seq', 13, true);


--
-- Name: signals_id_seq; Type: SEQUENCE SET; Schema: public; Owner: iabadvisors
--

SELECT pg_catalog.setval('public.signals_id_seq', 13, true);


--
-- Name: trades_id_seq; Type: SEQUENCE SET; Schema: public; Owner: iabadvisors
--

SELECT pg_catalog.setval('public.trades_id_seq', 13, true);


--
-- Name: feature_snapshots feature_snapshots_market_id_snapshot_time_key; Type: CONSTRAINT; Schema: public; Owner: iabadvisors
--

ALTER TABLE ONLY public.feature_snapshots
    ADD CONSTRAINT feature_snapshots_market_id_snapshot_time_key UNIQUE (market_id, snapshot_time);


--
-- Name: feature_snapshots feature_snapshots_pkey; Type: CONSTRAINT; Schema: public; Owner: iabadvisors
--

ALTER TABLE ONLY public.feature_snapshots
    ADD CONSTRAINT feature_snapshots_pkey PRIMARY KEY (id);


--
-- Name: markets markets_market_id_key; Type: CONSTRAINT; Schema: public; Owner: iabadvisors
--

ALTER TABLE ONLY public.markets
    ADD CONSTRAINT markets_market_id_key UNIQUE (market_id);


--
-- Name: markets markets_pkey; Type: CONSTRAINT; Schema: public; Owner: iabadvisors
--

ALTER TABLE ONLY public.markets
    ADD CONSTRAINT markets_pkey PRIMARY KEY (id);


--
-- Name: model_performance model_performance_model_name_model_version_evaluation_date_key; Type: CONSTRAINT; Schema: public; Owner: iabadvisors
--

ALTER TABLE ONLY public.model_performance
    ADD CONSTRAINT model_performance_model_name_model_version_evaluation_date_key UNIQUE (model_name, model_version, evaluation_date);


--
-- Name: model_performance model_performance_pkey; Type: CONSTRAINT; Schema: public; Owner: iabadvisors
--

ALTER TABLE ONLY public.model_performance
    ADD CONSTRAINT model_performance_pkey PRIMARY KEY (id);


--
-- Name: portfolio_snapshots portfolio_snapshots_pkey; Type: CONSTRAINT; Schema: public; Owner: iabadvisors
--

ALTER TABLE ONLY public.portfolio_snapshots
    ADD CONSTRAINT portfolio_snapshots_pkey PRIMARY KEY (id);


--
-- Name: predictions predictions_pkey; Type: CONSTRAINT; Schema: public; Owner: iabadvisors
--

ALTER TABLE ONLY public.predictions
    ADD CONSTRAINT predictions_pkey PRIMARY KEY (id);


--
-- Name: signals signals_pkey; Type: CONSTRAINT; Schema: public; Owner: iabadvisors
--

ALTER TABLE ONLY public.signals
    ADD CONSTRAINT signals_pkey PRIMARY KEY (id);


--
-- Name: trades trades_pkey; Type: CONSTRAINT; Schema: public; Owner: iabadvisors
--

ALTER TABLE ONLY public.trades
    ADD CONSTRAINT trades_pkey PRIMARY KEY (id);


--
-- Name: idx_features_market_time; Type: INDEX; Schema: public; Owner: iabadvisors
--

CREATE INDEX idx_features_market_time ON public.feature_snapshots USING btree (market_id, snapshot_time);


--
-- Name: idx_markets_outcome; Type: INDEX; Schema: public; Owner: iabadvisors
--

CREATE INDEX idx_markets_outcome ON public.markets USING btree (outcome);


--
-- Name: idx_markets_resolution_date; Type: INDEX; Schema: public; Owner: iabadvisors
--

CREATE INDEX idx_markets_resolution_date ON public.markets USING btree (resolution_date);


--
-- Name: idx_model_perf_date; Type: INDEX; Schema: public; Owner: iabadvisors
--

CREATE INDEX idx_model_perf_date ON public.model_performance USING btree (evaluation_date);


--
-- Name: idx_portfolio_snapshot_time; Type: INDEX; Schema: public; Owner: iabadvisors
--

CREATE INDEX idx_portfolio_snapshot_time ON public.portfolio_snapshots USING btree (snapshot_time);


--
-- Name: idx_predictions_market_time; Type: INDEX; Schema: public; Owner: iabadvisors
--

CREATE INDEX idx_predictions_market_time ON public.predictions USING btree (market_id, prediction_time);


--
-- Name: idx_signals_executed; Type: INDEX; Schema: public; Owner: iabadvisors
--

CREATE INDEX idx_signals_executed ON public.signals USING btree (executed);


--
-- Name: idx_signals_market; Type: INDEX; Schema: public; Owner: iabadvisors
--

CREATE INDEX idx_signals_market ON public.signals USING btree (market_id);


--
-- Name: idx_trades_entry_time; Type: INDEX; Schema: public; Owner: iabadvisors
--

CREATE INDEX idx_trades_entry_time ON public.trades USING btree (entry_time);


--
-- Name: idx_trades_market; Type: INDEX; Schema: public; Owner: iabadvisors
--

CREATE INDEX idx_trades_market ON public.trades USING btree (market_id);


--
-- Name: idx_trades_status; Type: INDEX; Schema: public; Owner: iabadvisors
--

CREATE INDEX idx_trades_status ON public.trades USING btree (status);


--
-- Name: feature_snapshots feature_snapshots_market_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: iabadvisors
--

ALTER TABLE ONLY public.feature_snapshots
    ADD CONSTRAINT feature_snapshots_market_id_fkey FOREIGN KEY (market_id) REFERENCES public.markets(market_id) ON DELETE CASCADE;


--
-- Name: predictions predictions_market_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: iabadvisors
--

ALTER TABLE ONLY public.predictions
    ADD CONSTRAINT predictions_market_id_fkey FOREIGN KEY (market_id) REFERENCES public.markets(market_id) ON DELETE CASCADE;


--
-- Name: signals signals_prediction_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: iabadvisors
--

ALTER TABLE ONLY public.signals
    ADD CONSTRAINT signals_prediction_id_fkey FOREIGN KEY (prediction_id) REFERENCES public.predictions(id) ON DELETE SET NULL;


--
-- Name: trades trades_signal_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: iabadvisors
--

ALTER TABLE ONLY public.trades
    ADD CONSTRAINT trades_signal_id_fkey FOREIGN KEY (signal_id) REFERENCES public.signals(id) ON DELETE SET NULL;


--
-- PostgreSQL database dump complete
--

\unrestrict wQ6RXHF6LkfSu0cKdYRMiXZZMSZZxmI5NPUugAiQV3UQkbfC2XjULspUjQjkoke


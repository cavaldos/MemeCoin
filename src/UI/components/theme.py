APP_CSS = """
Screen {
    background: #282c34;
}

Header {
    background: #21252b;
    color: #abb2bf;
}

#app-container {
    layout: vertical;
    height: 1fr;
}

#main-area {
    layout: horizontal;
    height: 1fr;
}

#navbar {
    width: 26;
    background: #21252b;
    border-right: tall #3e4451;
    padding: 0;
}

#nav-brand {
    height: 4;
    background: #61afef;
    content-align: center middle;
    padding: 0 1;
    color: #282c34;
    text-style: bold;
}

#nav-sep {
    margin: 0 1;
    color: #3e4451;
}

.nav-section-label {
    color: #5c6370;
    padding: 1 2 0 2;
    text-style: bold;
}

#uptime-display {
    color: #e5c07b;
    padding: 0 2 1 2;
    text-style: bold;
}

.nav-item {
    width: 100%;
    height: 3;
    padding: 0 2;
    content-align: left middle;
    background: transparent;
    color: #5c6370;
    border: none;
    text-style: none;
}

.nav-item:hover {
    background: #3e4451;
    color: #abb2bf;
}

.nav-item:focus {
    background: #3e4451;
    color: #abb2bf;
    text-style: none;
}

.nav-item.active {
    background: #2c313a;
    color: #61afef;
    text-style: bold;
    border-left: tall #61afef;
}

.nav-item.active:focus {
    background: #2c313a;
    color: #61afef;
    text-style: bold;
}

#content-area {
    width: 1fr;
    background: #282c34;
}

#content-header {
    height: 3;
    background: #21252b;
    content-align: left middle;
    padding: 0 2;
    border-bottom: tall #3e4451;
}

#content-header .title {
    text-style: bold;
    color: #abb2bf;
}

#content-header .breadcrumb {
    color: #5c6370;
}

#content-body {
    padding: 1 1;
}

.panel {
    height: auto;
    padding: 1 2;
    border: round #3e4451;
    background: #21252b;
    margin: 0 0 1 0;
}

.panel-title {
    color: #c678dd;
    text-style: bold;
    padding: 0 0 1 0;
}

.panel-muted {
    color: #5c6370;
}

.stat-row {
    width: 100%;
    height: auto;
    margin: 0 0 1 0;
}

.stat-card {
    width: 1fr;
    height: auto;
    background: #21252b;
    border: round #3e4451;
    margin: 0 0 0 1;
    padding: 0;
    text-align: center;
}

.stat-card:first-child {
    margin: 0;
}

.stat-card:hover {
    border: round #61afef;
}

.stat-label {
    color: #5c6370;
    text-style: bold;
}

.stat-value {
    color: #abb2bf;
    text-style: bold;
}

.stat-positive {
    color: #98c379;
    text-style: bold;
}

.stat-negative {
    color: #e06c75;
    text-style: bold;
}

.activity-item {
    height: auto;
    padding: 1 2;
    background: #21252b;
    border: round #3e4451;
    margin: 0 0 1 0;
}

.signal-buy {
    border-left: tall #98c379;
}

.signal-sell {
    border-left: tall #e06c75;
}

.source-card {
    height: auto;
    padding: 1 2;
    background: #21252b;
    border: round #3e4451;
    margin: 0 0 1 0;
}

.source-card:hover {
    border: round #c678dd;
}

.data-item {
    height: auto;
    padding: 0 2;
    margin: 0 0 0 0;
    color: #abb2bf;
}

Input {
    margin: 0 0 1 0;
    border: round #3e4451;
    background: #2c313a;
    color: #abb2bf;
}

Input:focus {
    border: round #61afef;
}

Input.-valid:focus {
    border: round #98c379;
}

Button {
    margin: 0 1 0 0;
    border: round #3e4451;
    background: #2c313a;
    color: #abb2bf;
}

Button:hover {
    background: #3e4451;
    border: round #61afef;
    color: #abb2bf;
}

Button:focus {
    border: round #61afef;
    color: #abb2bf;
}

Button.-primary {
    background: #61afef;
    color: #282c34;
    border: round #61afef;
}

Button.-primary:hover {
    background: #528bbd;
    border: round #528bbd;
    color: #282c34;
}

Button.-success {
    background: #98c379;
    color: #282c34;
    border: round #98c379;
}

Button.-success:hover {
    background: #7da362;
    border: round #7da362;
    color: #282c34;
}

Button.-error {
    background: #e06c75;
    color: #282c34;
    border: round #e06c75;
}

Button.-error:hover {
    background: #be5046;
    border: round #be5046;
    color: #282c34;
}

.btn-row {
    height: auto;
    layout: horizontal;
    margin: 1 0;
}

.coin-toggle {
    width: 100%;
    height: auto;
    background: #21252b;
    border: round #3e4451;
    margin: 0 0 1 0;
    padding: 0;
}

.coin-toggle:focus-within {
    border: round #61afef;
    background: #21252b;
}

.coin-toggle > CollapsibleTitle {
    color: #abb2bf;
    padding: 1 1;
    text-style: bold;
}

.coin-toggle > CollapsibleTitle:hover {
    background: #2c313a;
    color: #61afef;
}

.coin-toggle > CollapsibleTitle:focus {
    background: #2c313a;
    color: #61afef;
    text-style: bold;
}

.coin-toggle > Contents {
    padding: 0 1 1 3;
}

.coin-details {
    width: 100%;
    height: auto;
}

.coin-url {
    width: 100%;
    margin: 0 0 1 0;
    padding: 0 1;
    border: round #3e4451;
    background: #2c313a;
    color: #56b6c2;
}

Button.copy-url-button {
    width: 6;
    min-width: 6;
    margin: 0;
    padding: 0;
    border: none;
}

Button.copy-url-button.-primary {
    background: #61afef;
    color: #282c34;
    border: none;
}

Button.copy-url-button:hover {
    background: #528bbd;
    color: #282c34;
    border: none;
}

Button.copy-url-button:focus {
    background: #528bbd;
    color: #282c34;
    border: none;
}

.table-header {
    color: #5c6370;
    text-style: bold;
    padding: 0 0 1 0;
    border-bottom: solid #3e4451;
}

.table-row {
    padding: 1 0;
    color: #abb2bf;
    border-bottom: solid #2c313a;
}

.text-green { color: #98c379; }
.text-red { color: #e06c75; }
.text-yellow { color: #e5c07b; }
.text-muted { color: #5c6370; }
.text-bright { color: #abb2bf; }

Footer {
    background: #21252b;
    color: #5c6370;
}

Rule {
    color: #3e4451;
    margin: 1 0;
}
"""

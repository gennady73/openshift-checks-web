

# **openshift-checks-web**

A lightweight, Flask-based web interface for the openshift-checks diagnostic suite.

Designed for **disconnected environments**, this tool provides a UI to schedule, execute, and visualize OpenShift cluster health checks. It acts as a management wrapper around the shell-based [openshift-checks](https://github.com/gennady73/openshift-checks) engine, utilizing the **RISU framework** to render rich HTML reports from JSON data.

---

## **Features**\*

* **Web Dashboard:** A single-pane-of-glass to view the health status of your OpenShift cluster.  
* **Unified Reporting:** Converts complex shell script outputs into structured JSON and renders them via the RISU framework into readable HTML.  
* **Job Scheduler:** Integrated Flask-APScheduler to run diagnostic checks automatically at defined intervals (Cron-style).  
* **Scripts Editor:** A web-based editor to modify or create "tailored" shell scripts for custom diagnostic scenarios.  
* **Disconnected Ready:** Zero external dependencies required at runtime. All CSS/JS assets are bundled locally.  
* **"Call-Home" Architecture:**(under development) Decoupled reporting where check scripts push results back to the web application via HTTP POST.

\* See the ***[USER GUIDE](/docs/user-guide.md)*** for more information.  

---

## **Architecture**

The solution consists of three distinct components working together:

1. **openshift-checks-web (This Repo):** The Flask web application, UI, scheduler, and database.  
2. **openshift-checks (Fork):** The execution engine. Contains the shell scripts (checks/, info/) and the risu.py processor.  
3. **original (Upstream):** The RHsyseng base repository (reference only).

### **Data Flow**

1. **Scheduler/User** triggers a job in the Web UI.  
2. **Async Task** executes a shell script from the openshift-checks directory.  
3. **RISU Framework** processes the script output.  
4. **Call-Home:**(under development) The script sends the generated JSON report back to the Web UI via \--call-home.  
5. **Web UI** saves the result to SQLite and renders the HTML report.

---

## **Prerequisites**

* **Python 3.9+**  
* **OpenShift CLI (oc)**: Must be installed and authenticated on the host machine.  
* **Write Access**: The application requires write access to the local SQLite database file.  
* **Sibling Directory Structure**: The application expects the openshift-checks repository to exist parallel to this project.

---

## **Installation & Setup**

### **1\. Clone Repositories**

Ensure both the web project and the checks engine are cloned into the same parent directory:

```bash
mkdir openshift-diagnostics && cd openshift-diagnostics

# 1. Clone the engine (The Fork)  
git clone https://github.com/gennady73/openshift-checks.git

# 2. Clone the web interface  
git clone https://github.com/gennady73/openshift-checks-web.git
```

### **2\. Environment Setup (Disconnected)**

Create a virtual environment and install dependencies. *Note: In a disconnected environment, you may need to transfer the pip packages or use a local pypi mirror.*

- openshift-checks project  
    ```bash
    cd openshift-checks  
    python3 -m venv venv  
    source venv/bin/activate  
    pip install -r requirements.txt
    ``` 

- openshift-checks-web project
    ```bash
    cd openshift-checks-web  
    python3 -m venv venv  
    source venv/bin/activate  
    pip install -r requirements.txt
    ``` 

### **3\. Configuration**

Create a .env file or export the necessary environment variables:

```bash
# Path to the openshift-checks directory (Relative or Absolute)  
export CHECKS_BASE\_DIR="../openshift-checks"

# Flask Secret Key (for sessions)  
export SECRET_KEY="your-secret-key-here"

# Database Connection String  
export SQLALCHEMY_DATABASE_URI="sqlite:///app.db"
```

### **4\. Asset Consolidation**

To ensure the reports render correctly in disconnected mode, copy the static assets from the checks repo to the web repo:

```bash
cp -r ../openshift-checks/local-web-resources/*./static/
```

---

## **Usage**

### **Running Locally (Development)**

The following represents a basic use, see the ***[USER GUIDE](/docs/user-guide.md)*** for more information.  

```bash
export FLASK_ENV=development
export KUBECONFIG=/path/to/your/kubeconfig
export NSTALL_CONFIG_PATH=../openshift-checks/kubeconfig/install-config.yaml
export RISU_BASE=../openshift-checks
flask run \--host=0.0.0.0 \--port=5500
```

Access the dashboard at http://localhost:5500.

![Dashboard - Home blank](/docs/assets/home_blank.png)  


### **Running with Gunicorn (Production)**

*Warning: Due to SQLite locking, do not use multiple workers (-w) without configuring a scheduler lock.*

```bash
gunicorn app:app --bind 0.0.0.0:8080
```

### **Using the "Call-Home" Feature**(under development)

When creating custom checks or running risu.py manually, use the following flag to push results to the web dashboard:

```bash
./risu.py --call-home http://localhost:5000/api/callback/<RUN_ID>
```

---

## **Known Limitations & Notes**

1. **Scripts Editor:** The "Scripts Editor" modifies files directly in the openshift-checks directory. This may cause git pull conflicts if you attempt to update the engine from the upstream source.  
2. **Concurrency:** The application uses **SQLite**. High levels of concurrent usage or running multiple Gunicorn workers without careful configuration may lead to "Database Locked" errors.  
3. **Security:** The application allows the execution of shell scripts. Ensure the host machine is secured and access to the Web UI is restricted to authorized personnel only.

---

## **Contributing**

1. Fork the repository.  
2. Create a feature branch (git checkout \-b feature/amazing-feature).  
3. Commit your changes (git commit \-m 'Add some amazing feature').  
4. Push to the branch (git push origin feature/amazing-feature).  
5. Open a Pull Request.


---


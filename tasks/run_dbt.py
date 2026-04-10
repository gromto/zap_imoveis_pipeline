import subprocess

def run_dbt():
    result = subprocess.run(
        ["dbt", "run"],
        cwd="imoveis_dbt", 
        capture_output=True,
        text=True
    )

    print(result.stdout)

    if result.returncode != 0:
        raise Exception("dbt run failed")
    
if __name__ == "__main__":
    run_dbt()
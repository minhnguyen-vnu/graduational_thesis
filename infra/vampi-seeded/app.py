from config import vuln_app
import os

'''
 Decide if you want to server a vulnerable version or not!
 DO NOTE: some functionalities will still be vulnerable even if the value is set to 0
          as it is a matter of bad practice. Such an example is the debug endpoint.
'''
vuln = int(os.getenv('vulnerable', 1))
# vuln=1
# token alive for how many seconds?
alive = int(os.getenv('tokentimetolive', 60))

'''
 THESIS SEED (stateful/temporal authorization, bug class A1).
 When 0 (default) the app is VULNERABLE: authorization trusts the `admin` claim carried
 inside the already-issued JWT, so a demoted admin's old token keeps admin power until it
 expires. When 1 it is FIXED: the current role is re-read from the store on every request.
 Mirrors `app.security.stateful-role-check` in the Tier-1 target reports-api.
'''
stateful_role_check = int(os.getenv('statefulrolecheck', 0))


# start the app with port 5000 and debug on!
if __name__ == '__main__':
    vuln_app.run(host='0.0.0.0', port=5000, debug=True)

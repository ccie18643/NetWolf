# NetWolf

### Distributed network automation concept
<br>

NetWolf is a proof of concept for the distributed real-time network monitoring and automation system capable of simultaneously interacting with thousands of network devices using vertical and horizontal scaling resources. It consists of the manager program and the number of agents. Agents can be spread over multiple machines and bind separate processes to every available CPU core. Each of those processes maintains SSH connectivity to multiple network devices. To achieve a high number of connections per core and simultaneously consume the least possible memory, the agent is internally based on Asyncio. Agent registers with the manager and receives jobs containing the hostname for the network device it's supposed to connect to and the set of commands that need to execute. For monitoring, the job can also contain filters that must be applied to the command output before it's sent back to the manager.

For PoC, I have set it up to retrieve the CPU load from a couple hundred Cisco switches and routers. Currently, I was able to maintain around 350 SSH sessions using a single core and pulling fresh data from each device every second. With this approach, the number of monitored devices scales nicely with the number of CPU cores and the number of machines used by agents. NetWolf is in a very early stage of development and is nothing more than just a toy project. However, it also has an excellent potential to be helpful in the production environment once it's mature enough.

#### Already implemented:

 - *Simple hash-based load balancing of the monitored devices across multiple agents - load is being spread out over multiple agents dynamically to account for the number of agents registered with the manager at a given time.*
 - *Stateless job execution, SSH session to the monitored device is maintained as long as the agent periodically receives the 'job refresh' command. Once the agent stops being available, all the jobs it was responsible for are transferred to other agents. If the manager stops being available, agents age out the jobs and wait until the connectivity to the manager can be restored.*
 - *Simple management protocol transfers jobs and results between manager and agents (the NetJson class).*
 - *Ability for the agents to work on their jobs not being able to communicate with the manager for a limited time.*
 - *Currently, agents display the output data locally instead of sending it back to the manager. This is more convenient for debugging purposes at this early stage.*


#### To be implemented:

 - *Load balancing based on a consistent hash algorithm - this is not particularly useful for monitoring but may be more beneficial for automation purposes*
 - *Stateful job execution, the manager sends the job to the agent and keeps track of it till the report of completion is sent back, or it times out - useful for automation purposes*

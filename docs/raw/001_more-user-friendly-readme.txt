date: 2026-03-07
title: More User Friendly ReadMe
url: https://chatgpt.com/c/69abff01-f4e4-8325-ab49-364e54b275fe

Increase the show-to-tell ratio.


lionscliapp -- a tiny framework for building CLI tools that remember things


• data persistence
• CLI argument parsing
• swiss-army commands
• JSON I/O
• installation



data persistence

                       
  .mytool/                    
  ├── config.json             app.declare_projectdir(".mytool")
  ├── input/
  └── output/


CLI argument parsing

  args:
  * username                  app.declare_key("username", "anonymous")
  * path.inbox                app.declare_key("path.inbox", ".mytool/inbox")
  * path.outbox               app.declare_key("path.outbox", ".mytool/outbox")

                          mytool --username foo      (use for this invocation)
                          mytool set username foo    (keep in config.json)
                          mytool get username        (what value will it use?)
                          mytool keys                (list all configurable keys)


swiss-army knife commands

  def default_cmd():          app.declare_cmd("", default_cmd)
      ...                     app.describe_cmd("", "runs the app")

  def cmd_foo():              app.declare_cmd("foo", cmd_foo)
      ...                     app.describe_cmd("foo", "print 'foo' for the user")

  def cmd_bar():              app.declare_cmd("bar", cmd_bar)
      ...                     app.describe_cmd("bar", "write the username to a file in path.outbox")

                          mytool         <- runs default_cmd
                          mytool foo     <- runs cmd_foo
                          mytool --username x bar    <- writes 'x' to a file in path.outbox


JSON I/O

  .mytool/
  ├── config.json         app.declare_key("path.data", ".mytool/data.json")
  ├── data.json           
  ├── input/              D = app.read_json("data", "c")  # c = at configured location
  └── output/             app.write_json("data", D, "c2")  # 2 = 2-indented

                    Also:
                      app.write_json("c:/data.json", D, "f")  # f = filesystem: at specified path
                      app.write_json("data.json", D, "f")  # f = filesystem: at CWD
                      app.write_json("data.json", D, "e")  # e = execution root: (containing .mytool)
                      app.write_json("data.json", D, "p")  # p = project directory: (.mytool/data.json)


  

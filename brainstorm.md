# Commands

## Admin commands
- !space
    - add <name> <visibility> <required_role> <parent>: Create a space (or, if
      it exists and the bot is already an admin there, registers it in the
      database). Visibility is one of "public", "space" (only if it has a
      parent space) or "private", the role name can be set (or be "none") if
      the room is private, and the parent space (as an internal ID) is an
      optional space to create this new one in. If the space is private,
      creates a welcome room attached to it. Prints the new space internal ID,
      and the new welcome room ID, if applicable
    - name <space_id> <name>: changes the name of the space
    - description <space_id> <desc>: changes the description of a space
    - image <space_id> <mxc_id>: changes the image of the space
    - required_role <space_id> <role>: changes the required role of the space
    - visibility <space_id> <visibility>: changes the visibility. If already
      private, it can’t be set back to public or space
    - info <space_id>: prints information about a space (including its
      children)
    - delete <space_id>: ask confirmation, then, if the **same** user reacts a
      specific emoji, kick everyone out of the space and deletes it 
- !room
    - add <name> <visibility> <required_role> <space>: Create a room (or, if it
      exists, and the bot is already an admin there, registers it in the
      database). Visibility is one of "public", "space" (only if it has a
      parent space) or "private", the role name can be set (or be "none") if
      the room is private, and the parent space (as an internal ID) is an
      optional space to create this room in. Prints the new room internal ID.
    - name <room_id> <name>: changes the name of the room
    - description <room_id> <desc>: changes the description of a room
    - image <room_id> <mxc_id>: changes the image of the room
    - required_role <room_id> <role>: changes the required role of the room
    - visibility <room_id> <visibility>: changes the visibility. If already
      private, it can’t be set back to public or space
    - info <room_id>: prints information about a room (including its children)
    - delete <room_id>: ask confirmation, then, if the **same** user reacts a
      specific emoji, kick everyone out of the room and deletes it 
- !role_category
    - add <name> <admin_role> <parent>: creates a role category. The user must
      have the admin_role of the parent category if applicable
    - set_parent <name> <parent>: changes the hierarchy of the category. If the
      new parent is not "none", the user must be part of the parent’s
      admin_role
    - admin_role <name> <role>: changes the admin role of the category. The
      user must be part of both old and new roles
    - show <name>: displays the category and its contents recursively. If the
      name is omitted, displays root-level categories and roles (still
      recursively)
    - delete <name>: asks confirmation, then deletes the category. If there are
      roles inside, the roles are attached to the parent category (or root)
      before suppression. If there are role menus containing this category,
      they’re deactivated and the bots warns the user about them.
    - menu <role_category> <room> <prompt>: prints the role chooser menu in the
      chosen room, and listen to reacts to assign roles. If the category
      doesn’t contain any roles directly, the command fails
- !role
    - add <name> <emoji> <category>: creates a role. The emoji must be unique
      in this category (for the role menus). The category can be left blank. If
      there are role menus containing this category, they’re deactivated and
      the bot warns the user about hem.
    - description <role> <desc>: changes the description of a role. If there
      are role menus containing this role, they’re deactivated and the bot
      warns the user about hem.
    - emoji <role> <emoji>: changes the emoji for the role (must be unique in
      the category). If there are role menus containing this role, they’re
      deactivated and the bots warns the user about them.
    - name <role> <name>: changes the name of the role. If there are role menus
      containing this role, they’re deactivated and the bots warns the user
      about them.
    - category <role> <category>: changes the category of the role. The issuer
      must be part of the admin role of both old and new categories. The emoji
      must still be unique in the new category. If there are role menus
      containing this role, they’re deactivated and the bots warns the user
      about them.
    - delete <role>: asks confirmation, then deletes a role, **if** nobody has
      this role, or it isn’t used as a required role or admin role anywhere. If
      there are role menus containing this role, they’re deactivated and the
      bots warns the user about them.
    - assign <user> <role>: adds the requested role to the user. The issuer
      must have the admin role of the category
    - unassign <user> <role>: removes the requested role for the user. The
      issuer must have the admin role of the category
    - menu <role_category> <room> <prompt>: prints the role chooser menu in the
      chosen room, and listen to reacts to assign roles. If an existing menu
      for this category and this room exists, it’s deactivated
    - activate <role>: makes role usable. If there are role menus containing
      this role, they’re deactivated and the bot warns the user about them.
    - deactivate <role>: makes role unusable, **if** nobody has it. If there
      are role menus containing this role, they’re deactivated and the bot
      warns the user about them.
- !roles <user>: prints the chosen user active roles
- !reinvite: checks the active roles of the user and invites them back to
  spaces and rooms they’re not in

### Commands that need confirmation

!space delete
!room delete
!role delete
!role_category delete

### ACLs

Each command has a permission attached to it, that exists in database.
Permission are attached to roles. When a command is issued, the bot will check
if the user is part of a role that has this permission.

After checking permission, some commands will have a row-level check, for rooms
and roles for example. Creating a role in a category will need that the issuer
has the admin_role of the category.
  
## Standard commands
  
- !validate <user>: if the current room is a welcome room for a space, grants
  the user the required role for this space and invites them in
- !roles: prints the user actuve roles in a direct message
- !admin <duration>: grants (if they have the required permission) a higher
  powerlevel for the current room for a specific duration, then demotes them

# Config

```yaml
language: fr
confirmation_emojis:
    accept: ✅
    cancel: ❌
```
    

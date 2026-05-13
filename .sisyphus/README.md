# 📜 Project-Specific Agent Instructions

**Auto-loaded at session start**  
**Priority:** CRITICAL - Read before any work

---

## 🎯 MANDATORY WORKFLOW

Every agent working on this project MUST follow this sequence:

### Session Start
```
1. Read /home/ubuntu/bench/pro-secretary/TASK.md (get context)
2. Read /home/ubuntu/bench/pro-secretary/.sisyphus/RULES.md (understand rules)
3. Check current active tasks
4. Proceed with work
```

### Session End
```
1. Complete assigned work
2. Verify changes (tests, linting, etc.)
3. Update /home/ubuntu/bench/pro-secretary/TASK.md (MANDATORY - see RULES.md)
4. Report completion to user
```

---

## 🔄 TASK.md UPDATE REQUIREMENT

**CRITICAL:** After completing ANY work, you MUST update TASK.md with:

- ✅ Mark completed items
- 📝 Add to "Recently Completed" with timestamp
- 📋 Update "NEXT STEPS" 
- 💬 Add entry to "Communication Notes"
- 🕐 Update "Last Updated" timestamp

**See `.sisyphus/RULES.md` for detailed update protocol.**

---

## 🚨 BLOCKING RULES

1. **Never complete work without updating TASK.md**
2. **Always read TASK.md before starting work**
3. **Document all decisions in TASK.md**
4. **Update blockers/issues as discovered**

---

## 📍 Key Files

- `/home/ubuntu/bench/pro-secretary/TASK.md` - Main handoff document (READ FIRST)
- `/home/ubuntu/bench/pro-secretary/.sisyphus/RULES.md` - Detailed rules (READ SECOND)
- `/home/ubuntu/bench/pro-secretary/` - Project root

---

## 🎓 Quick Reference

**Starting work:**
```bash
read("/home/ubuntu/bench/pro-secretary/TASK.md")
read("/home/ubuntu/bench/pro-secretary/.sisyphus/RULES.md")
# Now you have full context
```

**Ending work:**
```bash
# After completing task
edit("/home/ubuntu/bench/pro-secretary/TASK.md", ...)  # Update with completion
# Report to user
```

---

**Compliance Level:** MANDATORY  
**Enforcement:** Every session, every agent, no exceptions
